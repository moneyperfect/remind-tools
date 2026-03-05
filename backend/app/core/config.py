import os

class Settings:
    app_name: str = "Task Manager API"
    app_version: str = "2.0.0"
    database_url: str = ""
    secret_key: str = "your-secret-key-change-in-production"
    token_expire_minutes: int = 60 * 24
    
    def __init__(self):
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.app_version = os.getenv("APP_VERSION", self.app_version)
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.database_url = os.path.join(base_dir, "tasks.db")

_settings = None

def get_settings():
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings