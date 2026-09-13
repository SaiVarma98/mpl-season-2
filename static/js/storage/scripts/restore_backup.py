import json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; BACKUPS=ROOT/'backups'
if len(sys.argv)!=2: raise SystemExit('Usage: python scripts/restore_backup.py backups/<folder>')
src=ROOT/sys.argv[1] if not Path(sys.argv[1]).is_absolute() else Path(sys.argv[1])
required=['players.json','teams.json','auction_groups.json','auction_state.json']
if not src.is_dir(): raise SystemExit(f'Backup folder not found: {src}')
for n in required:
    p=src/n
    if not p.exists(): raise SystemExit(f'Missing {n} in backup.')
    json.loads(p.read_text(encoding='utf-8'))
if input('RESTORE THIS BACKUP? type YES: ').strip()!='YES': raise SystemExit('Cancelled.')
for n in required: shutil.copy2(src/n,DATA/n)
print('Restored:',src)
