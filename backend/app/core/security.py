import re
from typing import List, Tuple, Optional
from pathlib import Path
from ..config import settings

class SecurityValidator:
    def __init__(self):
        self.dangerous_patterns = settings.dangerous_patterns
        self.blocked_env_vars = settings.blocked_env_vars
        
        # Regex for secret detection
        self.secret_patterns = [
            (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
            (r"sk-ant-[a-zA-Z0-9\-]{20,}", "Anthropic API Key"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub PAT"),
            (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"-----BEGIN (RSA )?PRIVATE KEY-----", "Private Key"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded Password"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API Key"),
        ]
    
    def is_command_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """Check if command is allowed"""
        cmd = command.strip()
        if not cmd:
            return False, "Empty command"
        
        # Check dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern in cmd:
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check for rm -rf with broad scope
        if re.search(r"rm\s+.*-rf\s+.*(/|\*|~)", cmd):
            if "/workspace" not in cmd and "./" not in cmd and "node_modules" not in cmd and "dist" not in cmd:
                # Allow rm -rf within workspace subdirectories but not root
                if re.search(r"rm\s+-rf\s+/$|rm\s+-rf\s+/\*|rm\s+-rf\s+~", cmd):
                    return False, "Destructive rm command blocked"
        
        # Check for git reset --hard without confirmation - allow but flag
        # For now, allow most commands but log
        # Extract base command
        base_cmd = cmd.split()[0]
        # Allow if in workspace context
        # We allow all for now with sandboxing, but dangerous ones require approval
        return True, None
    
    def requires_approval(self, command: str) -> bool:
        """Check if command requires user approval"""
        dangerous_keywords = [
            "rm ", "rmdir", "del ", "format", "git reset --hard",
            "DROP TABLE", "DELETE FROM", "TRUNCATE",
            "chmod 777", "chown"
        ]
        cmd_lower = command.lower()
        for kw in dangerous_keywords:
            if kw.lower() in cmd_lower:
                return True
        return False
    
    def detect_secrets(self, content: str) -> List[Tuple[str, str]]:
        """Detect secrets in content"""
        findings = []
        for pattern, desc in self.secret_patterns:
            matches = re.findall(pattern, content)
            for m in matches:
                # Don't include full secret in result
                findings.append((desc, f"{m[:10]}..."))
        return findings
    
    def sanitize_env(self, env: dict) -> dict:
        """Remove blocked env vars from exposure"""
        sanitized = {}
        for k, v in env.items():
            is_blocked = any(blocked.lower() in k.lower() for blocked in self.blocked_env_vars)
            if not is_blocked:
                sanitized[k] = v
            else:
                sanitized[k] = "***REDACTED***"
        return sanitized
    
    def validate_path(self, base: Path, target: Path) -> bool:
        """Ensure target is within base (prevent path traversal)"""
        try:
            base_resolved = base.resolve()
            target_resolved = target.resolve()
            return str(target_resolved).startswith(str(base_resolved))
        except:
            return False

security_validator = SecurityValidator()
