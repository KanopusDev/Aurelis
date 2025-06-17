"""Session management for Aurelis - handles user sessions and conversation history."""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from aurelis.core.types import SessionContext
from aurelis.core.config import get_config
from aurelis.core.logging import get_logger, get_audit_logger
from aurelis.core.cache import get_cache_manager
from aurelis.core.exceptions import AurelisError


@dataclass
class ConversationEntry:
    """Single entry in conversation history."""
    timestamp: datetime
    user_input: str
    system_response: str
    command: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionPreferences:
    """User preferences for a session."""
    preferred_model: Optional[str] = None
    chunking_strategy: Optional[str] = None
    analysis_types: List[str] = field(default_factory=list)
    output_format: str = "table"
    auto_save: bool = True
    verbose: bool = False


class SessionManager:
    """Manages user sessions and conversation history."""
    
    def __init__(self):
        self.logger = get_logger("session")
        self.audit_logger = get_audit_logger()
        self.cache_manager = get_cache_manager()
        self.config = get_config()
        
        # Active sessions
        self.active_sessions: Dict[str, SessionContext] = {}
        
        # Session storage
        self.session_dir = Path.home() / ".aurelis" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(
        self,
        user_id: Optional[str] = None,
        project_path: Optional[Path] = None,
        preferences: Optional[SessionPreferences] = None
    ) -> SessionContext:
        """Create a new user session."""
        session_id = str(uuid.uuid4())
        
        # Create session context
        session = SessionContext(
            session_id=session_id,
            user_id=user_id,
            project_path=project_path,
            preferences=preferences.model_dump() if preferences else {}
        )
        
        # Store in active sessions
        self.active_sessions[session_id] = session
        
        # Save session to disk
        self._save_session(session)
        
        # Log session creation
        if self.audit_logger:
            self.audit_logger.log_command_execution(
                "create_session",
                user_id=user_id,
                session_id=session_id,
                success=True,
                metadata={
                    "project_path": str(project_path) if project_path else None,
                    "has_preferences": preferences is not None
                }
            )
        
        self.logger.info(f"Created session {session_id} for user {user_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get session by ID."""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Try to load from disk
        session = self._load_session(session_id)
        if session:
            self.active_sessions[session_id] = session
        
        return session
    
    def update_session(self, session: SessionContext) -> None:
        """Update session data."""
        session.last_activity = datetime.now()
        
        # Update in active sessions
        self.active_sessions[session.session_id] = session
        
        # Save to disk
        self._save_session(session)
    
    def close_session(self, session_id: str) -> bool:
        """Close and cleanup session."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Save final state
        self._save_session(session)
        
        # Remove from active sessions
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        # Log session closure
        if self.audit_logger:
            self.audit_logger.log_command_execution(
                "close_session",
                user_id=session.user_id,
                session_id=session_id,
                success=True,
                metadata={
                    "duration_minutes": (datetime.now() - session.created_at).total_seconds() / 60,
                    "conversation_entries": len(session.conversation_history)
                }
            )
        
        self.logger.info(f"Closed session {session_id}")
        return True
    
    def add_conversation_entry(
        self,
        session_id: str,
        user_input: str,
        system_response: str,
        command: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add entry to conversation history."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        entry = ConversationEntry(
            timestamp=datetime.now(),
            user_input=user_input,
            system_response=system_response,
            command=command,
            metadata=metadata or {}
        )
        
        # Add to conversation history
        session.conversation_history.append(entry.model_dump() if hasattr(entry, 'model_dump') else {
            'timestamp': entry.timestamp.isoformat(),
            'user_input': entry.user_input,
            'system_response': entry.system_response,
            'command': entry.command,
            'metadata': entry.metadata
        })
        
        # Update session
        self.update_session(session)
        
        return True
    
    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationEntry]:
        """Get conversation history for session."""
        session = self.get_session(session_id)
        if not session:
            return []
        
        history = session.conversation_history
        if limit:
            history = history[-limit:]
        
        return [
            ConversationEntry(
                timestamp=datetime.fromisoformat(entry['timestamp']),
                user_input=entry['user_input'],
                system_response=entry['system_response'],
                command=entry.get('command'),
                metadata=entry.get('metadata', {})
            )
            for entry in history
        ]
    
    def add_active_file(self, session_id: str, file_path: Path) -> bool:
        """Add file to session's active files."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        if file_path not in session.active_files:
            session.active_files.append(file_path)
            self.update_session(session)
        
        return True
    
    def remove_active_file(self, session_id: str, file_path: Path) -> bool:
        """Remove file from session's active files."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        if file_path in session.active_files:
            session.active_files.remove(file_path)
            self.update_session(session)
        
        return True
    
    def update_preferences(
        self,
        session_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update session preferences."""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.preferences.update(preferences)
        self.update_session(session)
        
        return True
    
    def cleanup_expired_sessions(self, max_age_days: int = 30) -> int:
        """Clean up expired sessions."""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0
        
        # Clean up session files
        for session_file in self.session_dir.glob("*.json"):
            try:
                import json
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                last_activity = datetime.fromisoformat(session_data.get('last_activity', '1970-01-01'))
                
                if last_activity < cutoff_time:
                    session_file.unlink()
                    cleaned_count += 1
                    
                    # Remove from active sessions if present
                    session_id = session_file.stem
                    if session_id in self.active_sessions:
                        del self.active_sessions[session_id]
            
            except Exception as e:
                self.logger.error(f"Error cleaning up session file {session_file}: {e}")
        
        # Clean up old active sessions
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.last_activity < cutoff_time:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            cleaned_count += 1
        
        self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count
    
    def get_active_sessions(self) -> List[SessionContext]:
        """Get all active sessions."""
        return list(self.active_sessions.values())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_sessions = len(list(self.session_dir.glob("*.json")))
        active_sessions = len(self.active_sessions)
        
        # Calculate average session duration for active sessions
        total_duration = sum(
            (datetime.now() - session.created_at).total_seconds()
            for session in self.active_sessions.values()
        )
        avg_duration = total_duration / active_sessions if active_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "average_session_duration_minutes": avg_duration / 60,
            "session_storage_path": str(self.session_dir)
        }
    
    def _save_session(self, session: SessionContext) -> None:
        """Save session to disk."""
        session_file = self.session_dir / f"{session.session_id}.json"
        
        try:
            import json
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "project_path": str(session.project_path) if session.project_path else None,
                "active_files": [str(f) for f in session.active_files],
                "conversation_history": session.conversation_history,
                "preferences": session.preferences,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
        except Exception as e:
            self.logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def _load_session(self, session_id: str) -> Optional[SessionContext]:
        """Load session from disk."""
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        try:
            import json
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Convert paths back to Path objects
            project_path = Path(session_data["project_path"]) if session_data.get("project_path") else None
            active_files = [Path(f) for f in session_data.get("active_files", [])]
            
            return SessionContext(
                session_id=session_data["session_id"],
                user_id=session_data.get("user_id"),
                project_path=project_path,
                active_files=active_files,
                conversation_history=session_data.get("conversation_history", []),
                preferences=session_data.get("preferences", {}),
                created_at=datetime.fromisoformat(session_data["created_at"]),
                last_activity=datetime.fromisoformat(session_data["last_activity"])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load session {session_id}: {e}")
            return None


class InteractiveSession:
    """Interactive session handler for continuous conversations."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_manager = get_session_manager()
        self.logger = get_logger("session.interactive")
        
        # Get or create session
        self.session = self.session_manager.get_session(session_id)
        if not self.session:
            raise AurelisError(f"Session not found: {session_id}")
    
    def process_input(
        self,
        user_input: str,
        command: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process user input and return response."""
        # This would integrate with the AI models and tools
        # For now, return a simple response
        
        response = f"Processed: {user_input}"
        
        # Add to conversation history
        self.session_manager.add_conversation_entry(
            self.session_id,
            user_input,
            response,
            command,
            metadata
        )
        
        return response
    
    def get_context(self) -> Dict[str, Any]:
        """Get session context for AI processing."""
        return {
            "session_id": self.session_id,
            "project_path": str(self.session.project_path) if self.session.project_path else None,
            "active_files": [str(f) for f in self.session.active_files],
            "preferences": self.session.preferences,
            "conversation_length": len(self.session.conversation_history)
        }
    
    def add_file_to_context(self, file_path: Path) -> bool:
        """Add file to session context."""
        return self.session_manager.add_active_file(self.session_id, file_path)
    
    def remove_file_from_context(self, file_path: Path) -> bool:
        """Remove file from session context."""
        return self.session_manager.remove_active_file(self.session_id, file_path)
    
    def update_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update session preferences."""
        return self.session_manager.update_preferences(self.session_id, preferences)
    
    def get_conversation_summary(self, last_n: int = 10) -> str:
        """Get summary of recent conversation."""
        history = self.session_manager.get_conversation_history(self.session_id, last_n)
        
        if not history:
            return "No conversation history"
        
        summary_parts = []
        for entry in history:
            summary_parts.append(f"User: {entry.user_input[:100]}...")
            summary_parts.append(f"Assistant: {entry.system_response[:100]}...")
        
        return "\n".join(summary_parts)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def initialize_session_manager() -> SessionManager:
    """Initialize the global session manager."""
    global _session_manager
    _session_manager = SessionManager()
    return _session_manager


def create_interactive_session(
    user_id: Optional[str] = None,
    project_path: Optional[Path] = None,
    preferences: Optional[SessionPreferences] = None
) -> InteractiveSession:
    """Create a new interactive session."""
    session_manager = get_session_manager()
    session = session_manager.create_session(user_id, project_path, preferences)
    return InteractiveSession(session.session_id)
