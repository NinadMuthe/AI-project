# backend/app/services/model_registry.py
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

CHECKPOINTS_DIR = Path(__file__).resolve().parents[2] / "model_checkpoints"
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory registry tracking model state per user
# user_id -> {"lstm": {...}, "isolation_forest": {...}}
_USER_MODEL_STATUS: Dict[int, Dict[str, Dict[str, Any]]] = {}


def get_checkpoint_path(user_id: int) -> Path:
    return CHECKPOINTS_DIR / f"user_{user_id}_lstm.pt"


def get_user_models_status(user_id: int) -> Dict[str, Any]:
    user_status = _USER_MODEL_STATUS.get(user_id, {})
    lstm_info = user_status.get("lstm", {
        "state": "not_enough_data",
        "last_trained_at": None,
        "records_used": 0,
        "message": "Requires at least 60 days of expense history",
    })
    anomaly_info = user_status.get("isolation_forest", {
        "state": "not_enough_data",
        "last_trained_at": None,
        "records_used": 0,
        "message": "Requires at least 30 transactions",
    })
    return {
        "lstm": lstm_info,
        "isolation_forest": anomaly_info,
    }


def update_model_status(
    user_id: int,
    model_type: str,
    state: str,
    records_used: int = 0,
    message: Optional[str] = None,
):
    if user_id not in _USER_MODEL_STATUS:
        _USER_MODEL_STATUS[user_id] = {}
    _USER_MODEL_STATUS[user_id][model_type] = {
        "state": state,  # not_enough_data | training | ready | failed
        "last_trained_at": datetime.utcnow().isoformat() if state == "ready" else _USER_MODEL_STATUS[user_id].get(model_type, {}).get("last_trained_at"),
        "records_used": records_used,
        "message": message,
    }


def should_retrain(user_id: int, model_type: str, current_record_count: int) -> bool:
    user_status = _USER_MODEL_STATUS.get(user_id, {})
    model_info = user_status.get(model_type)
    if not model_info or model_info.get("state") != "ready":
        return True
    last_count = model_info.get("records_used", 0)
    if last_count == 0:
        return True
    # Retrain when count changes by >= 20%
    return abs(current_record_count - last_count) / last_count >= 0.20

