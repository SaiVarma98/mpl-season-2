# Step 13 Changes

1. Viewer uses stronger high-contrast panels, overlays, shadows and typography
   so text remains readable against stadium/village backgrounds.
2. Default bid increment is now ₹1,000.
3. Every selected lot opens at its configured base price.
4. The first team to bid accepts the lot at base price; the increment is not
   added to the opening bid.
5. Auctioneer selects the increment first (₹50/₹100/₹200/₹500/₹1,000/custom).
6. Clicking a team automatically places that team's bid using the selected
   increment.
7. After a leading team exists, each new team click adds the selected
   increment.
8. The selected increment is persisted in auction_state.json.
