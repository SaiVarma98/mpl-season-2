from functools import wraps

from flask import Blueprint, jsonify, request, session, current_app

from services.api_service import APIService
from services.auction_engine import AuctionError
from services.sale_service import SaleError
from services.rollback_service import RollbackError
from services.lot_flow_service import LotFlowError
from services.lifecycle_service import LifecycleError

api_bp = Blueprint("api", __name__, url_prefix="/api")


def success(result):
    return jsonify(result), 200


def failure(message, status=400):
    return jsonify({
        "success": False,
        "message": message,
        "errors": []
    }), status


def auctioneer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "auctioneer":
            return failure("Auctioneer authentication required.", 401)
        return fn(*args, **kwargs)
    return wrapper


def service_from_app():
    return APIService(current_app.extensions['mpl_repository'])


def handle(fn):
    try:
        return fn()
    except (
        AuctionError,
        SaleError,
        RollbackError,
        LotFlowError,
        LifecycleError,
    ) as exc:
        return failure(str(exc), 400)
    except Exception:
        # Do not leak server internals to the public API.
        return failure("Internal server error.", 500)


@api_bp.post("/auction/start")
@auctioneer_required
def start():
    return handle(lambda: success(service_from_app().start()))


@api_bp.post("/auction/select")
@auctioneer_required
def select():
    body = request.get_json(silent=True) or {}
    group_id = body.get("group_id")
    if not group_id:
        return failure("group_id is required.")
    return handle(lambda: success(service_from_app().select(group_id)))



@api_bp.post("/auction/restart-lot")
@auctioneer_required
def restart_lot():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") is not True:
        return failure("Restart current lot confirmation is required.")
    return handle(lambda: success(service_from_app().restart_current_lot()))


@api_bp.post("/auction/increment")
@auctioneer_required
def set_increment():
    body = request.get_json(silent=True) or {}
    increment = body.get("increment")
    if increment is None:
        return failure("increment is required.")
    return handle(lambda: success(service_from_app().set_increment(increment)))


@api_bp.post("/auction/bid")
@auctioneer_required
def bid():
    body = request.get_json(silent=True) or {}
    team_id = body.get("team_id")
    if not team_id:
        return failure("team_id is required.")
    return handle(lambda: success(service_from_app().bid(team_id)))


@api_bp.post("/auction/sell")
@auctioneer_required
def sell():
    return handle(lambda: success(service_from_app().sell()))


@api_bp.post("/auction/pass")
@auctioneer_required
def pass_lot():
    return handle(lambda: success(service_from_app().pass_lot()))


@api_bp.post("/auction/hold")
@auctioneer_required
def hold():
    return handle(lambda: success(service_from_app().hold_lot()))


@api_bp.post("/auction/pause")
@auctioneer_required
def pause():
    return handle(lambda: success(service_from_app().pause()))


@api_bp.post("/auction/resume")
@auctioneer_required
def resume():
    return handle(lambda: success(service_from_app().resume()))


@api_bp.post("/auction/rollback")
@auctioneer_required
def rollback():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") is not True:
        return failure("Rollback confirmation is required.")
    return handle(lambda: success(service_from_app().rollback()))


@api_bp.post("/auction/reset")
@auctioneer_required
def reset():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") is not True:
        return failure("Reset confirmation is required.")

    from storage.backup import create_auction_backup
    return handle(lambda: success(
        service_from_app().reset(create_auction_backup)
    ))


@api_bp.post("/auction/round2")
@auctioneer_required
def round2():
    return handle(lambda: success(service_from_app().round2()))


@api_bp.post("/auction/end")
@auctioneer_required
def end():
    body = request.get_json(silent=True) or {}
    if body.get("confirm") is not True:
        return failure("End-auction confirmation is required.")
    return handle(lambda: success(service_from_app().end()))


@api_bp.get("/state")
def state():
    return handle(lambda: success(service_from_app().state()))


@api_bp.get("/players")
def players():
    return handle(lambda: success(service_from_app().players()))


@api_bp.get("/groups")
def groups():
    return handle(lambda: success(service_from_app().groups()))


@api_bp.get("/groups/current")
def current_group():
    return handle(lambda: success(service_from_app().current_group()))


@api_bp.get("/statistics")
def statistics():
    return handle(lambda: success(service_from_app().statistics()))


@api_bp.get("/history")
def history():
    return handle(lambda: success(service_from_app().history()))
