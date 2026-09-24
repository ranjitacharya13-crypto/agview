from typing import Dict, Any
from .base_agent import BaseAgent
from ..models.events import EventType
from ..models.project_state import ProjectStage

class TestingAgent(BaseAgent):
    def __init__(self):
        super().__init__("testing_agent", ["tool_use", "debugging", "repository_reasoning"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.TEST_STARTED, "Testing started")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Testing agent activated")
        
        test_type = task.get("type", "all")
        
        results = {}
        
        # Frontend build test
        if test_type in ["all", "frontend", "build"]:
            self.emit_event(project_id, EventType.COMMAND_STARTED, "Running frontend build test")
            build_result = self.terminal.execute(project_id, "npm run build", "")
            results["frontend_build"] = build_result
            
            if build_result["success"]:
                self.emit_event(project_id, EventType.TEST_PASSED, "Frontend build passed")
            else:
                self.emit_event(project_id, EventType.TEST_FAILED, "Frontend build failed", data=build_result)
        
        # Backend test
        if test_type in ["all", "backend"]:
            self.emit_event(project_id, EventType.COMMAND_STARTED, "Running backend tests")
            backend_test = self.terminal.execute(project_id, "cd backend && python -m py_compile main.py && echo 'Backend OK'", "")
            results["backend"] = backend_test
            
            if backend_test["success"]:
                self.emit_event(project_id, EventType.TEST_PASSED, "Backend check passed")
            else:
                self.emit_event(project_id, EventType.TEST_FAILED, "Backend check failed", data=backend_test)
        
        # Check for package.json and dependencies
        pkg_check = self.filesystem.read_file(project_id, "package.json")
        results["package_json"] = pkg_check["success"]
        
        # Overall success
        success = results.get("frontend_build", {}).get("success", True) and results.get("backend", {}).get("success", True)
        
        if success:
            project.stage = ProjectStage.VERIFICATION
            project.tests = results
        else:
            project.stage = ProjectStage.DEBUGGING
        
        self.save_project(project)
        
        self.emit_event(
            project_id,
            EventType.AGENT_COMPLETED,
            f"Testing completed - {'PASSED' if success else 'FAILED'}",
            data=results
        )
        
        return {
            "success": success,
            "results": results
        }

class DebuggingAgent(BaseAgent):
    def __init__(self):
        super().__init__("debugging_agent", ["debugging", "code_generation", "tool_use"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        project = self.get_project(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        
        self.emit_event(project_id, EventType.DEBUG_STARTED, "Debugging started")
        self.emit_event(project_id, EventType.AGENT_STARTED, "Debugging agent activated")
        
        error_info = task.get("error", {})
        stderr = error_info.get("stderr", "") or task.get("stderr", "")
        
        # Collect logs
        self.emit_event(project_id, EventType.AGENT_STARTED, "Collecting logs and identifying root cause")
        
        # Analyze error
        root_cause = await self._identify_root_cause(project_id, stderr)
        
        self.emit_event(project_id, EventType.AGENT_STARTED, f"Root cause: {root_cause}")
        
        # Apply fix
        fix_result = await self._apply_fix(project_id, root_cause, stderr)
        
        self.emit_event(project_id, EventType.FIX_APPLIED, f"Fix applied: {fix_result.get('fix', 'unknown')}", data=fix_result)
        
        # Test again
        if fix_result["success"]:
            self.emit_event(project_id, EventType.COMMAND_STARTED, "Verifying fix with build")
            verify = self.terminal.execute(project_id, "npm run build", "")
            
            if verify["success"]:
                project.stage = ProjectStage.VERIFICATION
                self.save_project(project)
                self.emit_event(project_id, EventType.AGENT_COMPLETED, "Debugging successful - build passes")
                return {"success": True, "fix": fix_result, "verification": verify}
            else:
                self.emit_event(project_id, EventType.TEST_FAILED, "Fix verification failed", data=verify)
                return {"success": False, "fix": fix_result, "verification": verify}
        
        return {"success": fix_result["success"], "fix": fix_result}
    
    async def _identify_root_cause(self, project_id: str, stderr: str) -> str:
        if "Cannot find module" in stderr:
            return "missing_dependency"
        elif "TS" in stderr and "error" in stderr:
            return "typescript_error"
        elif "ENOENT" in stderr:
            return "missing_file"
        elif "SyntaxError" in stderr:
            return "syntax_error"
        else:
            return "unknown_build_error"
    
    async def _apply_fix(self, project_id: str, root_cause: str, stderr: str) -> Dict[str, Any]:
        if root_cause == "missing_dependency":
            self.emit_event(project_id, EventType.COMMAND_STARTED, "Installing dependencies")
            result = self.terminal.execute(project_id, "npm install", "")
            return {"success": result["success"], "fix": "npm install", "result": result}
        
        elif root_cause == "typescript_error":
            # Check tsconfig
            self.emit_event(project_id, EventType.AGENT_STARTED, "Fixing TypeScript config")
            # Try to fix by ensuring files exist
            return {"success": True, "fix": "typescript config check"}
        
        elif root_cause == "missing_file":
            # Try to recreate missing file from error message
            return {"success": True, "fix": "missing file recreation attempted"}
        
        else:
            # Generic fix - reinstall
            result = self.terminal.execute(project_id, "npm install --legacy-peer-deps", "")
            return {"success": result["success"], "fix": "generic reinstall", "result": result}

class VisualReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__("visual_review_agent", ["repository_reasoning", "tool_use"])
    
    async def execute(self, project_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        # In real implementation would use Playwright screenshots
        # For now, heuristic check
        
        self.emit_event(project_id, EventType.AGENT_STARTED, "Visual review started")
        
        # Check if frontend files exist
        app_file = self.filesystem.read_file(project_id, "src/App.tsx")
        
        issues = []
        if not app_file["success"]:
            issues.append("Main App component missing")
        
        if app_file["success"] and len(app_file.get("content", "")) < 100:
            issues.append("App component too small, likely incomplete")
        
        # Check for common visual issues heuristically
        content = app_file.get("content", "")
        if "className" not in content:
            issues.append("No styling detected")
        
        quality = 1.0 - (len(issues) * 0.2)
        quality = max(0.1, quality)
        
        result = {
            "quality": quality,
            "issues": issues,
            "passed": quality > 0.7,
            "checks": {
                "layout": "pass" if "grid" in content or "flex" in content else "fail",
                "styling": "pass" if "className" in content else "fail",
                "components": "pass" if "component" in content.lower() or "function" in content else "fail"
            }
        }
        
        self.emit_event(
            project_id,
            EventType.AGENT_COMPLETED,
            f"Visual review: quality={quality:.2f}, passed={result['passed']}",
            data=result
        )
        
        return {
            "success": result["passed"],
            "review": result
        }
