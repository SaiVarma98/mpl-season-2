# MPL Season 2 — Event Readiness Pass

## Verified / hardened
1. Auction flow services validated with the sample JSON dataset: reset, start,
   select, base-price opening bid, multiple team bids, sell, pause/resume,
   rollback, round 2 and end.
2. Bid increment is server-authoritative. `/api/auction/bid` no longer accepts
   a client-supplied increment; it uses the persisted `auction_state.json`
   `bid_increment` value.
3. First team bid is exactly the lot base price. Later team clicks add the
   persisted increment.
4. Viewer SOLD presentation is protected against the 500ms polling loop
   repeatedly restarting the SOLD screen. It stays for ~4.5 seconds and then
   returns to the waiting/summary view until the next lot is selected.
5. Team-wise sold summary is calculated from sold groups and displays each
   purchased player's name and the completed lot price.
6. RESET, ROLLBACK and END require both authenticated Auctioneer access and a
   server-side `confirm: true` request for the destructive actions.
7. Auctioneer lifecycle controls are collapsed under MANAGE AUCTION; primary
   bidding actions remain prominent.
8. Viewer and Auctioneer show reconnection state without blinking the last good
   content.
9. `scripts/event_readiness_check.py` validates player/group/team/state
   relationships and flags whether the production player count is exactly 96.
10. `scripts/backup_now.py` and `scripts/restore_backup.py` provide a simple
    event-day JSON backup/restore procedure.

## Important production-data status
The packaged sample data currently contains **10 players**, because only 10
MPL player records were supplied in the working project. The validator will
report this as a warning. Replace `data/players.json` with the complete 96-player
MPL Season 2 production file before the live event; the application does not
invent the missing 86 records.

## Event-day procedure
1. Run `python scripts/event_readiness_check.py`.
2. Require zero ERRORS. For production, also require `Players: 96`.
3. Run `python scripts/backup_now.py` and keep the backup folder on the same
   machine plus a USB copy.
4. Start Flask.
5. Open `/auctioneer` on the operator laptop and `/viewer` on the LED/projector.
6. Use the Auctioneer to set the desired increment. It is persisted server-side.
7. Test one sample lot before the event starts, then RESET and confirm the data
   is pristine.
