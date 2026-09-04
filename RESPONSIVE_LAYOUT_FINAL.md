# Responsive layout final fix

The previous build still contained older TV-oriented rules that could win the cascade
for player image positioning and section sizing.

This final layer is intentionally appended last and establishes a strict document-flow
layout:

HEADER
LOT BAR
STAGE (players + bid)
TEAM STRIP

Player images occupy only the image portion of each player card. Player information has
a dedicated bottom region. The team strip is a separate grid row and cannot overlap the
player stage.

The layout uses the actual browser viewport and reflows for narrow screens. No auction
logic, API, polling, sale, team, player, or branding behavior was changed.
