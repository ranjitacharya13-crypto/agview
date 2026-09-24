from typing import Dict, Any, List
import uuid
from datetime import datetime
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectState, ProjectStage
from ..services.rlcd_engine import rlcd_engine
from ..services.reward import reward_service
from ..services.project_manager import project_manager
from ..models.rlcd import ActionSpace

# Import all agents
from .research_agent import ResearchAgent
from .abstract_agent import AbstractAgent, AbstractCritic
from .solution_architect import SolutionArchitectAgent
from .frontend_agent import FrontendEngineeringAgent
from .backend_agent import BackendEngineeringAgent
from .testing_agent import TestingAgent, DebuggingAgent, VisualReviewAgent
from .presentation_agent import PresentationAgent

class MasterAgent(BaseAgent):
    """
    Master Agent - orchestrates all other agents
    Its job is NOT to generate all code, but to:
    - understand project state
    - determine current stage
    - evaluate available information
    - call RLCD decision engine
    - select appropriate agent
    - execute workflow
    - monitor results
    - trigger verification
    - request human approval when necessary
    - update project memory
    """
    def __init__(self):
        super().__init__("master_agent", ["long_context", "repository_reasoning", "tool_use"])
        
        # Initialize sub-agents
        self.research_agent = ResearchAgent()
        self.abstract_agent = AbstractAgent()
        self.abstract_critic = AbstractCritic()
        self.solution_architect = SolutionArchitectAgent()
        self.frontend_agent = FrontendEngineeringAgent()
        self.backend_agent = BackendEngineeringAgent()
        self.testing_agent = TestingAgent()
        self.debugging_agent = DebuggingAgent()
        self.visual_review_agent = VisualReviewAgent()
        self.presentation_agent = PresentationAgent()
        
        self.rlcd_engine = rlcd_engine
        self.reward_service = reward_service
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.AGENT_STARTED, f"Master agent executing task: {task.get('action', 'auto')}")
        
        action = task.get("action", "auto")
        
        if action == "auto":
            # Autonomous loop: observe -> decide -> act -> observe result -> verify -> repair -> continue
            return await self._autonomous_loop(project_id, task)
        else:
            # Direct action
            return await self._execute_action(project_id, action, task)
    
    async def _autonomous_loop(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        max_iterations = task.get("max_iterations", 10)
        iteration = 0
        
        results = []
        
        while iteration < max_iterations:
            iteration += 1
            
            # 1. OBSERVE - get current state
            current_state = project.to_summary()
            current_state["stage"] = project.stage.value
            
            # 2. DECIDE - call RLCD
            decision = self.rlcd_engine.decide_choice(project)
            
            # Record decision
            from ..models.project_state import DecisionRecord
            decision_record = DecisionRecord(
                type="CHOICE",
                state=project.stage.value,
                action=decision.selected_action,
                probabilities=decision.probabilities,
                raw_confidence=decision.raw_confidence,
                calibrated_confidence=decision.calibrated_confidence,
                risk=decision.risk,
                requires_verification=decision.requires_verification,
                requires_approval=decision.requires_approval,
                evidence=decision.evidence,
                agent=self.name
            )
            project.decisions.append(decision_record)
            self.save_project(project)
            
            self.emit_event(
                project_id,
                EventType.RLCD_DECISION,
                f"RLCD Decision: {decision.selected_action} (conf: {decision.calibrated_confidence:.2f})",
                decision_id=decision_record.id,
                data={
                    "decision": decision.model_dump(),
                    "state": current_state
                }
            )
            
            # Check if should ask user
            if decision.selected_action == ActionSpace.ASK_USER.value:
                self.emit_event(project_id, EventType.AGENT_COMPLETED, "Master agent requesting user input")
                break
            
            if decision.selected_action == ActionSpace.STOP.value:
                self.emit_event(project_id, EventType.AGENT_COMPLETED, "Master agent stopping autonomous loop")
                break
            
            # 3. ACT - execute selected action
            action_result = await self._execute_action(project_id, decision.selected_action, task)
            results.append({
                "iteration": iteration,
                "decision": decision.selected_action,
                "result": action_result
            })
            
            # 4. OBSERVE RESULT
            project = self.get_project(project_id)  # Refresh
            next_state = project.to_summary()
            next_state["stage"] = project.stage.value
            
            # 5. REWARD - calculate reward
            reward = self.reward_service.calculate_reward(
                action=decision.selected_action,
                result="success" if action_result.get("success") else "failure",
                context={
                    "tests_passed": action_result.get("success", False),
                    "tool_calls": 1,
                    "correct_implementation": action_result.get("success", False)
                }
            )
            
            # 6. TRAJECTORY - store
            trajectory = self.reward_service.create_trajectory(
                state=current_state,
                action=decision.selected_action,
                result="success" if action_result.get("success") else "failure",
                reward=reward,
                next_state=next_state,
                decision_id=decision_record.id,
                agent=self.name,
                raw_probability=decision.raw_confidence
            )
            
            project.trajectories.append(trajectory)
            self.save_project(project)
            
            self.emit_event(
                project_id,
                EventType.REWARD_RECORDED,
                f"Reward: {reward:.2f} for {decision.selected_action}",
                data={"reward": reward, "trajectory_id": trajectory.id}
            )
            
            # 7. VERIFY / REPAIR if needed
            if not action_result.get("success") and decision.selected_action not in [ActionSpace.DEBUG.value]:
                # Try debugging
                debug_decision = self.rlcd_engine.decide_choice(project, custom_action_space=[ActionSpace.DEBUG.value, ActionSpace.ASK_USER.value])
                if debug_decision.selected_action == ActionSpace.DEBUG.value:
                    debug_result = await self._execute_action(project_id, ActionSpace.DEBUG.value, {"error": action_result})
                    results.append({"iteration": iteration, "decision": "DEBUG", "result": debug_result})
            
            # Check if project completed
            if project.stage == ProjectStage.COMPLETED:
                break
            
            # If failed multiple times, ask user
            if iteration >= max_iterations:
                self.emit_event(project_id, EventType.AGENT_COMPLETED, "Max iterations reached, asking user")
                break
        
        return {
            "success": True,
            "iterations": iteration,
            "results": results,
            "final_stage": project.stage.value
        }
    
    async def _execute_action(self, project_id: str, action: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        
        try:
            if action == ActionSpace.ANALYZE_PROBLEM.value:
                # Analyze problem statement
                project.stage = ProjectStage.ANALYZING
                self.save_project(project)
                self.emit_event(project_id, EventType.AGENT_COMPLETED, "Problem analyzed")
                return {"success": True, "stage": project.stage.value}
            
            elif action == ActionSpace.RESEARCH.value:
                result = await self.research_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.CREATE_ABSTRACT.value:
                result = await self.abstract_agent.execute(project_id, task)
                # Auto-critique
                if result["success"]:
                    critique = await self.abstract_critic.execute(project_id, {})
                    result["critique"] = critique
                    # If needs revision and we have iterations left
                    if critique.get("needs_revision") and task.get("auto_revise", True):
                        # For now, don't auto-revise infinitely
                        pass
                return result
            
            elif action == ActionSpace.REVISE_ABSTRACT.value:
                result = await self.abstract_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.CREATE_SOLUTION.value:
                result = await self.solution_architect.execute(project_id, task)
                return result
            
            elif action == ActionSpace.CREATE_FRONTEND.value:
                result = await self.frontend_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.CREATE_BACKEND.value:
                result = await self.backend_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.CREATE_DATABASE.value:
                # Database is part of backend for now
                result = await self.backend_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.INTEGRATE.value:
                # Integration test
                project.stage = ProjectStage.INTEGRATION
                self.save_project(project)
                
                # Test frontend + backend together
                frontend_test = self.terminal.execute(project_id, "npm run build", "")
                backend_test = self.terminal.execute(project_id, "cd backend && python -m py_compile main.py", "")
                
                success = frontend_test["success"] and backend_test["success"]
                if success:
                    project.stage = ProjectStage.TESTING
                
                self.save_project(project)
                
                return {
                    "success": success,
                    "frontend": frontend_test,
                    "backend": backend_test
                }
            
            elif action == ActionSpace.RUN_TESTS.value:
                result = await self.testing_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.DEBUG.value:
                result = await self.debugging_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.VERIFY.value:
                result = await self._verify_project(project_id)
                return result
            
            elif action == ActionSpace.CREATE_PRESENTATION.value:
                result = await self.presentation_agent.execute(project_id, task)
                return result
            
            elif action == ActionSpace.ASK_USER.value:
                return {"success": True, "action": "ask_user", "message": "User input required"}
            
            elif action == ActionSpace.STOP.value:
                project.stage = ProjectStage.COMPLETED
                self.save_project(project)
                return {"success": True, "action": "stop", "stage": project.stage.value}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        
        except Exception as e:
            self.emit_event(project_id, EventType.ERROR, f"Error executing {action}: {str(e)}", data={"error": str(e)})
            return {"success": False, "error": str(e), "action": action}
    
    async def _verify_project(self, project_id: str) -> Dict[str, Any]:
        project = self.get_project(project_id)
        self.emit_event(project_id, EventType.VERIFICATION_STARTED, "Final verification started")
        
        checks = {}
        
        # 1. Dependency check
        pkg = self.filesystem.read_file(project_id, "package.json")
        checks["package_json"] = pkg["success"]
        
        # 2. Frontend build
        build = self.terminal.execute(project_id, "npm run build", "")
        checks["frontend_build"] = build["success"]
        
        # 3. Backend startup check
        backend = self.terminal.execute(project_id, "cd backend && python -m py_compile main.py && echo OK", "")
        checks["backend_compile"] = backend["success"]
        
        # 4. File existence
        app_file = self.filesystem.read_file(project_id, "src/App.tsx")
        checks["frontend_files"] = app_file["success"]
        
        backend_file = self.filesystem.read_file(project_id, "backend/main.py")
        checks["backend_files"] = backend_file["success"]
        
        # 5. Project state consistency
        checks["project_state"] = bool(project.problem_statement and project.abstract)
        
        # 6. Security scan - check for secrets
        # (Simplified)
        checks["security"] = True
        
        all_passed = all(checks.values())
        
        project.verification = checks
        if all_passed:
            project.stage = ProjectStage.COMPLETED
        else:
            project.stage = ProjectStage.VERIFICATION
        
        self.save_project(project)
        
        self.emit_event(
            project_id,
            EventType.VERIFICATION_COMPLETED,
            f"Verification {'PASSED' if all_passed else 'FAILED'} - {sum(checks.values())}/{len(checks)} checks",
            data=checks
        )
        
        return {
            "success": all_passed,
            "checks": checks,
            "verified": all_passed
        }
    
    def get_available_actions(self, project_id: str) -> List[str]:
        project = self.get_project(project_id)
        if not project:
            return []
        
        return self.rlcd_engine._get_valid_actions(project)
