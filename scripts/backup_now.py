import json, shutil
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; OUT=ROOT/'backups'/('manual_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
OUT.mkdir(parents=True,exist_ok=False)
for name in ['players.json','teams.json','auction_groups.json','auction_state.json']:
    shutil.copy2(DATA/name,OUT/name)
print(OUT)
