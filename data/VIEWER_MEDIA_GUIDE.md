# Viewer Media Setup

Edit `viewer_media.json`.

## Main logo
Set:
` tournament.main_logo_url `

Use the existing public MPL logo URL.

## Sponsor logos
For each sponsor:
- `name`
- `logo_url`
- `tier`

## Sponsor videos
Each video:
- `video_url`: public MP4/WebM URL
- `poster_url`: optional poster image
- `enabled`: true/false
- `muted`: true for autoplay
- `loop`: true/false
- `display_seconds`: rotation duration

Do not upload or manage S3 from Flask. The browser directly loads public media
URLs, consistent with the player-image approach.
