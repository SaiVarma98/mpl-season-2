from flask import Blueprint, jsonify
from pathlib import Path
import json

viewer_api_bp = Blueprint("viewer_api", __name__, url_prefix="/api/viewer")


def _media():
    path = Path(__file__).resolve().parents[1] / "data" / "viewer_media.json"
    if not path.exists():
        return {"tournament": {}, "sponsors": [], "videos": []}
    return json.loads(path.read_text(encoding="utf-8"))


@viewer_api_bp.get("/media")
def media():
    return jsonify({
        "success": True,
        "message": "Viewer media loaded.",
        "data": _media()
    })
