from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    app_name: str = "RLCD Agentic Engineering IDE"
    version: str = "1.0.0"
    debug: bool = True
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    workspace_root: Path = base_dir / "workspace"
    data_root: Path = base_dir / "backend" / "data"
    projects_root: Path = data_root / "projects"
    
    # Security
    allowed_commands: List[str] = [
        "npm", "npx", "yarn", "pnpm",
        "python", "python3", "pip", "pip3",
        "node", "git", "ls", "cat", "echo",
        "mkdir", "touch", "pwd", "cd",
        "pytest", "jest", "tsc", "vite",
        "code", "ls", "find", "grep",
        "curl", "wget", "chmod", "cp", "mv"
    ]
    dangerous_patterns: List[str] = [
        "rm -rf /",
        "rm -rf /*",
        ":(){:|:&};:",
        "mkfs",
        "dd if=",
        "shutdown",
        "reboot",
        "> /dev/sda",
        "chmod 777 /",
        "curl | sh",
        "wget | sh"
    ]
    blocked_env_vars: List[str] = [
        "AWS_SECRET", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "GITHUB_TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY"
    ]
    
    # RLCD
    max_iterations: int = 50
    max_tool_calls: int = 100
    max_cost: float = 10.0
    max_runtime_seconds: int = 3600
    
    # Model providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    default_model: str = "mock"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
settings.workspace_root.mkdir(parents=True, exist_ok=True)
settings.projects_root.mkdir(parents=True, exist_ok=True)
(settings.data_root / "trajectories").mkdir(parents=True, exist_ok=True)
(settings.data_root / "calibration").mkdir(parents=True, exist_ok=True)
