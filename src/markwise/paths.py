from pathlib import Path
from platformdirs import user_data_dir
from markwise.app_info import APP_NAME

DATA_DIR = Path(user_data_dir(APP_NAME, APP_NAME))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "markwise.db"
