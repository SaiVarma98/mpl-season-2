from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
BACKUP_DIR = BASE_DIR / 'backups'
SECRET_KEY = os.environ.get('MPL_SECRET_KEY', 'change-this-secret-before-production')
POLL_INTERVAL_MS = 500
