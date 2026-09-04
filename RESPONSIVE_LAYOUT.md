# Responsive Viewer Layout

The Viewer is now responsive to the actual browser viewport rather than assuming a fixed TV/projector canvas.

Supported behavior:
- Desktop / large LED display
- 16:9 screens
- 16:10 laptops
- 4:3 / unusual projector ratios
- Short-height landscape screens
- Tablets
- Portrait/mobile screens

The layout uses fluid sizing, `clamp()`, grid/flex reflow and media queries.
At narrow widths the player cards stack and the team strip becomes horizontally scrollable instead of overlapping content.

No auction API, polling, bid, sell, team, player, or branding logic was changed.
