from pathlib import Path

from platformdirs import user_data_dir

from markwise.app_info import APP_NAME

# Per-user data folder: ~/.local/share/MarkWise (Linux), %LOCALAPPDATA%\MarkWise (Windows)
DATA_DIR = Path(user_data_dir(APP_NAME, APP_NAME))
DB_PATH = DATA_DIR / "markwise.db"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def resource_path(*parts: str) -> Path:
    """Path to a file inside the markwise package (works in source and packaged builds)."""
    return Path(__file__).resolve().parent.joinpath(*parts)
