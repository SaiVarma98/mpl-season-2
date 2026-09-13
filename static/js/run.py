from app import app

if __name__ == '__main__':
    # threaded=True lets the server handle multiple requests concurrently.
    # This matters a lot here: viewer/big-screen displays poll /api/state
    # every second on their own, and without threading every one of those
    # polls is served one-at-a-time, so an auctioneer's bid/select click can
    # get stuck queued behind a viewer's poll request. The transaction()
    # lock in storage/json_storage.py already ensures mutating actions
    # (bid, sell, select, ...) are still serialized safely against each
    # other, so enabling threading here is safe.
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
