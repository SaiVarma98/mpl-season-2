# MPL Viewer Branding Final

Branding behavior:
- MPL header is fixed and remains visible in LIVE, WAITING, PAUSED, SOLD and COMPLETED states.
- Sponsor logo slots remain visible on both sides of the MPL title.
- `data/viewer_media.json -> tournament.main_logo_url` is used for the real MPL logo when configured.
- If the real logo URL is blank/unavailable, the MPL badge fallback remains visible.
- Sponsor logo URLs are rendered from `viewer_media.json`; blank slots show sponsor placeholders.
- State overlays begin below the header, so they no longer cover/dim the MPL title and sponsor row.
- No auction logic, polling interval, or state transitions were changed.
