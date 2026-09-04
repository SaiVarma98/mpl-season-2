# MPL Refactor & Verification

## Refactor fixes
- Viewer SOLD overlay is now driven by the persisted `LOT_SOLD` state, not by the last historical SOLD event. This fixes SOLD -> next-lot transition.
- Auctioneer refresh no longer requests `/api/groups` twice.
- Added `scripts/verify_auction_flow.py` for repeatable service-layer event-day verification.

## Verified service flow
- Start
- Select single lot
- First bid equals base price
- Server-authoritative increment
- Multiple-team bid
- Sell
- Winning-team purse deduction
- Winning-team player assignment
- Player sold/team assignment
- Next lot selection after SOLD
- Pass
- Pause / Resume
- Rollback restoration

The Flask endpoint test could not be executed in this build environment because Flask is not installed in the available Python runtime. The service-layer auction flow passed independently.
