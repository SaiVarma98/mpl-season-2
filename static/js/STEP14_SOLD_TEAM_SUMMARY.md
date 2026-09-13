# Step 14 — Team-wise Sold Players Viewer Summary

The public Viewer now includes a team-wise SOLD PLAYERS summary.

For each of the five teams it shows:
- Team logo
- Team name
- Number of players purchased
- Player names
- Sale price for each player/lot

Player photos are intentionally NOT shown in this summary.

The summary is populated from the persisted auction groups and current team
data, so it reflects completed sales rather than duplicating auction data.

It appears while the auction is waiting between lots after at least one sale.
The normal live auction, SOLD presentation, pause, and completed screens remain
unchanged.

No new backend storage file is introduced.
