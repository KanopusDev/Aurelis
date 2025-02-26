import json
from pathlib import Path
from typing import Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)

class Config:
    CONFIG_DIR = Path.home() / ".aurelis"
    CONFIG_FILE = CONFIG_DIR / "config.json"
    DB_PATH = CONFIG_DIR / "database"
    LOG_DIR = CONFIG_DIR / "logs"

    @classmethod
    def load(cls) -> Dict:
        try:
            if not cls.CONFIG_FILE.exists():
                return {}
            with open(cls.CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {}

    @classmethod
    def save(cls, config: Dict):
        try:
            cls.CONFIG_DIR.mkdir(exist_ok=True)
            with open(cls.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            logger.error(f"Failed to save config: {str(e)}")
            raise

    @classmethod
    def get_api_key(cls, key_name: str) -> Optional[str]:
        config = cls.load()
        return config.get(key_name)

    @classmethod
    def get_db_path(cls) -> Path:
        """Get the database directory path."""
        # Create the directory if it doesn't exist
        path = cls.DB_PATH
        path.mkdir(exist_ok=True, parents=True)
        return path
        
    @classmethod
    def get_log_path(cls) -> Path:
        """Get the default log directory path."""
        # Check for environment variable first
        env_path = os.environ.get("AURELIS_LOG_DIR")
        if env_path:
            path = Path(env_path)
        else:
            # Use default path
            path = cls.LOG_DIR
            
        # Create directory if it doesn't exist
        path.mkdir(exist_ok=True, parents=True)
        return path
        
    @classmethod
    def set_log_path(cls, path: Path) -> None:
        """Save custom log path to configuration."""
        config = cls.load()
        config["log_dir"] = str(path)
        cls.save(config)
