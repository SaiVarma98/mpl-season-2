"""Static regression checks for the MPL Viewer.

This does not require Flask/browser dependencies. It catches the exact
SELL -> CONNECTION LOST regression and verifies photo-positioning rules.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "templates" / "viewer.html").read_text(encoding="utf-8")

def require(text, label):
    if text not in HTML:
        raise AssertionError(f"Missing: {label}")

require('id="lastSaleText"', "last-sale DOM target")
require('const lastSale=$("lastSaleText"); if(lastSale)', "defensive last-sale update")
require('object-position:center center !important', "centered player photo positioning")
require('object-fit:contain !important', "non-cropping player photo sizing")
require('state.auction_status==="LOT_SOLD"', "state-driven SOLD rendering")
require('renderLive(data);', "live rendering after SOLD")

print("Viewer regression checks: PASS")
