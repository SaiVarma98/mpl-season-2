from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

from repositories.auction_repository import AuctionRepository
from repositories.user_repository import UserRepository
from config import DATA_DIR, SECRET_KEY
from routes.api_routes import api_bp
from routes.viewer_routes import viewer_api_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=SECRET_KEY, DATA_DIR=DATA_DIR)
    if test_config:
        app.config.update(test_config)

    repository = AuctionRepository(app.config["DATA_DIR"])
    user_repository = UserRepository(app.config["DATA_DIR"])

    app.extensions['mpl_repository'] = repository
    app.register_blueprint(api_bp)
    app.register_blueprint(viewer_api_bp)

    @app.get("/login")
    def login_page():
        return render_template("login.html")

    @app.post("/api/auth/login")
    def login():
        # This is a one-time, local village auction application. Credentials are
        # intentionally kept simple in users.json; no password-hash dependency
        # is required for the local event build.
        body = request.get_json(silent=True) or {}
        username = str(body.get("username", ""))
        password = str(body.get("password", ""))

        user = user_repository.find(username)
        if not user or user.get("role") != "auctioneer":
            return jsonify({"success": False, "message": "Invalid credentials.", "errors": []}), 401

        if password != str(user.get("password", "")):
            return jsonify({"success": False, "message": "Invalid credentials.", "errors": []}), 401

        session.clear()
        session["username"] = username
        session["role"] = "auctioneer"
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "data": {"username": username, "role": "auctioneer"}
        })

    @app.post("/api/auth/logout")
    def logout():
        session.clear()
        return jsonify({"success": True, "message": "Logged out.", "data": {}})

    @app.get("/auctioneer")
    def auctioneer():
        if session.get("role") != "auctioneer":
            from flask import redirect
            return redirect("/login")
        return render_template("auctioneer.html")

    @app.get("/viewer")
    def viewer():
        return render_template("viewer.html")

    return app


app = create_app()


@app.route("/team-squads")
def team_squads():
    return render_template("team_squads.html")


if __name__ == "__main__":
    app.run(debug=True)
