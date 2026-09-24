import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Callable, Any, Set
from collections import defaultdict
from ..models.events import ProjectEvent, EventType

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, Set[Callable]] = defaultdict(set)
        self.event_history: Dict[str, List[ProjectEvent]] = defaultdict(list)
        self.max_history = 1000
    
    def emit(self, project_id: str, event_type: EventType, message: str = "", 
             agent: str = None, decision_id: str = None, data: Dict[str, Any] = None) -> ProjectEvent:
        event = ProjectEvent(
            id=str(uuid.uuid4())[:8],
            project_id=project_id,
            type=event_type,
            timestamp=datetime.now(),
            agent=agent,
            decision_id=decision_id,
            data=data or {},
            message=message
        )
        
        # Store in history
        self.event_history[project_id].append(event)
        if len(self.event_history[project_id]) > self.max_history:
            self.event_history[project_id] = self.event_history[project_id][-self.max_history:]
        
        # Notify subscribers
        for callback in self.subscribers[project_id]:
            try:
                callback(event)
            except Exception as e:
                print(f"Event callback error: {e}")
        
        # Also notify global subscribers
        for callback in self.subscribers["*"]:
            try:
                callback(event)
            except Exception as e:
                print(f"Global event callback error: {e}")
        
        return event
    
    def subscribe(self, project_id: str, callback: Callable):
        self.subscribers[project_id].add(callback)
    
    def unsubscribe(self, project_id: str, callback: Callable):
        self.subscribers[project_id].discard(callback)
    
    def get_history(self, project_id: str, limit: int = 100) -> List[ProjectEvent]:
        history = self.event_history.get(project_id, [])
        return history[-limit:]
    
    def get_all_history(self, project_id: str) -> List[ProjectEvent]:
        return self.event_history.get(project_id, [])

event_bus = EventBus()
