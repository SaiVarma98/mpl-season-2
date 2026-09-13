# MPL — Mana Ooru Premier League Season 2
## Final Cricket Auction System

A focused, one-time village cricket auction application built with Flask,
JSON storage, Jinja2, TailwindCSS CDN, DaisyUI CDN and vanilla JavaScript.

The visual design is intentionally **premium professional-cricket-broadcast
style**, while keeping MPL's own village-tournament identity. It does not use
IPL trademarks, assets or infrastructure.

## Two user-facing interfaces

### Auctioneer — `/auctioneer`
Login required. Controls the entire auction.

### Viewer — `/viewer`
Public and read-only. Designed for a 1920×1080 LED/projector display.

There is no Admin Portal, bidder login, team login or bidder device flow.

## Features included

- Auctioneer session authentication.
- Password hash validation.
- Single / Duo / Trio auction groups.
- Five teams with ₹100,000 default purse.
- Base-price and purse validation.
- +₹50 / +₹100 / +₹200 / +₹500 / custom increments.
- Sell / Pass / Hold.
- Round 2.
- Pause / Resume.
- Last-sale rollback using a complete pre-sale snapshot.
- Reset with pre-reset backup.
- End auction.
- JSON history inside `auction_state.json`.
- Atomic JSON file replacement.
- Server restart recovery from JSON.
- 500ms AJAX polling.
- Public read-only Viewer APIs.
- Connection-lost/reconnect display.
- Rich Auctioneer control-room UI.
- 1920×1080 broadcast-style Viewer UI.
- Single / Duo / Trio player layouts.
- Sold presentation.
- Pause presentation.
- Completed presentation.
- Sponsor logo slots.
- Sponsor video slots.
- Main MPL logo slot.
- Village-cricket / stadium / gold-particle visual backgrounds.
- Responsive laptop/tablet fallback.
- No countdown.
- No WebSockets / Socket.IO / SSE.
- No database or external server infrastructure.

## Data

The package includes the current sample/working JSON data available in this
project, including the provided MPL player records and sample auction groups.
If the remaining registered MPL Season 2 players are available in your real
`players.json`, replace the sample file before the event. The application does
not invent missing production players.

Existing S3 player image URLs are rendered directly by the browser.

## Sponsor setup

Edit:

`data/viewer_media.json`

Configure:

- `tournament.main_logo_url`
- sponsor `logo_url` values
- sponsor names and tiers
- sponsor `video_url` values
- optional poster URLs
- video rotation duration

Videos should normally be public MP4/WebM URLs and muted for reliable browser
autoplay. Flask does not upload or manage media.

## Login

Development credentials:

```text
username: auctioneer
password: auction123
```

For the actual event, change the password hash in `data/users.json` and set a
strong `MPL_SECRET_KEY` environment variable.

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Run:

```bash
python run.py
```

Then open:

- `http://127.0.0.1:5000/login`
- `http://127.0.0.1:5000/auctioneer`
- `http://127.0.0.1:5000/viewer`

## Production event checklist

1. Put the final 96-player `players.json` into `data/`.
2. Verify every player has the correct S3 `photo_url`.
3. Verify `auction_groups.json` from the existing Club Manager.
4. Verify the five final team names, logos and owners.
5. Verify every team has `default_purse: 100000`.
6. Add the real MPL logo.
7. Add the real sponsor logos.
8. Add sponsor video URLs.
9. Set a production secret key.
10. Run the application once locally and verify `/login`, `/auctioneer` and
    `/viewer`.
11. Use RESET before the event if the sample data has been used for rehearsal.
12. Take a copy of the complete `data/` directory before going live.

## Project structure

```text
mpl-auction/
├── app.py
├── config.py
├── run.py
├── requirements.txt
├── data/
│   ├── players.json
│   ├── auction_groups.json
│   ├── teams.json
│   ├── users.json
│   ├── auction_state.json
│   └── viewer_media.json
├── models/
├── repositories/
├── services/
├── routes/
├── storage/
├── templates/
└── static/
    ├── css/
    ├── js/
    └── media/
```

No test-case folder is included in the final event build, as requested.


## Local Auctioneer Login

For this one-time local event build, `data/users.json` stores the Auctioneer credential directly. Default development credential:

- Username: `auctioneer`
- Password: `auction123`

No Werkzeug password-hash validation is used.
