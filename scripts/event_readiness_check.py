import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'
def load(n): return json.loads((DATA/n).read_text(encoding='utf-8'))
players=load('players.json'); teams=load('teams.json'); groups=load('auction_groups.json'); state=load('auction_state.json'); users=load('users.json')
errors=[]; warnings=[]
if len(players)!=96: warnings.append(f'players.json contains {len(players)} players; production acceptance requires exactly 96.')
ids=[str(p.get('id')) for p in players]
if len(ids)!=len(set(ids)): errors.append('Duplicate player IDs found.')
known=set(ids)
for g in groups:
    typ=str(g.get('type','')).lower(); expected={'single':1,'duo':2,'trio':3}.get(typ)
    if expected and len(g.get('players',[]))!=expected: errors.append(f'{g.get("group_id")}: {typ} requires {expected} players.')
    for pid in g.get('players',[]):
        if str(pid) not in known: errors.append(f'{g.get("group_id")}: player {pid} does not exist.')
team_ids=[str(t.get('id')) for t in teams]
if len(teams)!=5: errors.append(f'Expected 5 teams; found {len(teams)}.')
if len(team_ids)!=len(set(team_ids)): errors.append('Duplicate team IDs found.')
for t in teams:
    if int(t.get('default_purse',0))!=100000: errors.append(f'{t.get("team_name")}: default purse is not ₹100,000.')
if state.get('countdown') is not None or state.get('timer') is not None: errors.append('Countdown/timer state found; remove it.')
if not users or any('password_hash' in u for u in users): warnings.append('users.json contains hashed credentials; current local build expects direct local-event credentials.')
print('MPL EVENT READINESS CHECK')
print(f'Players: {len(players)} | Teams: {len(teams)} | Groups: {len(groups)}')
print('ERRORS:', len(errors)); [print(' -',e) for e in errors]
print('WARNINGS:', len(warnings)); [print(' -',w) for w in warnings]
if errors: sys.exit(2)
if warnings: sys.exit(1)
print('READY')
