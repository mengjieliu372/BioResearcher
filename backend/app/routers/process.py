from fastapi import APIRouter, Header
from pathlib import Path
import json
import os
from datetime import datetime
from app.auth_core import ensure_project_access, require_user

router = APIRouter()

Experiments_File = Path(__file__).parent.parent / "data" / "experiments.json"
RUNTIME_STALE_SECONDS = int(os.getenv("RUNTIME_STALE_SECONDS", "900"))
RUNTIME_STALE_SECONDS_HEAVY = int(os.getenv("RUNTIME_STALE_SECONDS_HEAVY", "3600"))
RUNTIME_STALE_SECONDS_CODING = int(os.getenv("RUNTIME_STALE_SECONDS_CODING", "7200"))


def _completed_flags(experiment: dict):
    return [
        bool(experiment.get('page_search_paper', False)) and bool(experiment.get('page_search_datasets', False)),
        bool(experiment.get('page_Literature_processing', False)),
        all(bool(experiment.get(k, False)) for k in ['page_design_1', 'page_design_2', 'page_design_3']),
        all(bool(experiment.get(k, False)) for k in ['page_dry_1', 'page_dry_2', 'page_dry_3']),
        # Current pipeline only executes coding for v3; mark Programming done by page_coding_3.
        bool(experiment.get('page_coding_3', False)),
    ]


def _checkpoint_stage(checkpoint: str):
    cp = (checkpoint or "").lower()
    if cp.startswith("search_") or cp in {"start", "queued", "prepare_dirs"}:
        return 0
    if cp.startswith("literature"):
        return 1
    if cp.startswith("design_"):
        return 2
    if cp.startswith("dry_"):
        return 3
    if cp.startswith("coding_"):
        return 4
    return None


def _stale_timeout_for_checkpoint(checkpoint: str) -> int:
    cp = (checkpoint or "").lower()
    if cp.startswith("coding_"):
        return RUNTIME_STALE_SECONDS_CODING
    if cp.startswith("literature") or cp.startswith("design_") or cp.startswith("dry_"):
        return RUNTIME_STALE_SECONDS_HEAVY
    return RUNTIME_STALE_SECONDS


def _available_versions(expid: int, kind: str):
    data_dir = Path(__file__).parent.parent / "data" / str(expid)
    if not data_dir.exists():
        return []
    out = []
    if kind == "dry":
        for p in data_dir.glob("dry_experiment*.json"):
            stem = p.stem  # dry_experiment3
            digits = "".join(ch for ch in stem if ch.isdigit())
            if digits:
                out.append(int(digits))
    elif kind == "coding":
        for p in data_dir.glob("coding*"):
            if p.is_dir():
                digits = "".join(ch for ch in p.name if ch.isdigit())
                if digits:
                    out.append(int(digits))
    return sorted(set(out))


def _stage_progresses(experiment: dict, runtime: dict, expid: int):
    completed = _completed_flags(experiment)
    progresses = [100 if c else 0 for c in completed]
    checkpoint_stage = _checkpoint_stage(runtime.get("checkpoint", ""))
    running_stage = checkpoint_stage
    gp = float(runtime.get("progress") or 0)
    dry_available = _available_versions(expid, "dry")
    coding_available = _available_versions(expid, "coding")
    dry_total = len(dry_available) if len(dry_available) > 0 else 3
    coding_total = len(coding_available) if len(coding_available) > 0 else 3
    if not completed[2]:
        done = sum(bool(experiment.get(k, False)) for k in ['page_design_1', 'page_design_2', 'page_design_3'])
        progresses[2] = max(progresses[2], min(100, int((done / 3.0) * 100)))
    if not completed[3]:
        done = sum(bool(experiment.get(k, False)) for k in ['page_dry_1', 'page_dry_2', 'page_dry_3'])
        progresses[3] = max(progresses[3], min(100, int((done / float(dry_total)) * 100)))
    if not completed[4]:
        done = sum(bool(experiment.get(k, False)) for k in ['page_coding_1', 'page_coding_2', 'page_coding_3'])
        progresses[4] = max(progresses[4], min(100, int((done / float(coding_total)) * 100)))

    if runtime.get("running") and running_stage == 0 and not completed[0]:
        progresses[0] = max(0, min(100, int((gp / 34.0) * 100)))
    elif runtime.get("running") and running_stage == 1 and not completed[1]:
        progresses[1] = max(0, min(100, int(((gp - 34.0) / 28.0) * 100)))
    return progresses, running_stage


@router.get("/{id}/process")
async def get_process(id: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    with Experiments_File.open() as f:
        experiments = json.load(f)
    experiment = next((exp for exp in experiments if exp["id"] == id), None)
    if experiment is None:
        return {"message": f"Experiment {id} not found", "completed_steps": []}
    completed_steps = [i for i, v in enumerate(_completed_flags(experiment)) if v]
    status_path = Path(__file__).parent.parent / "data" / str(id) / "runtime_status.json"
    runtime = {
        "running": False,
        "progress": 0,
        "message": "Idle",
        "checkpoint": "init",
        "error": None,
        "updated_at": "",
    }
    if status_path.exists():
        try:
            with status_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            runtime.update(data)
        except Exception:
            pass

    if runtime.get("running"):
        updated_at = runtime.get("updated_at") or ""
        stale = False
        if not updated_at:
            stale = True
        else:
            try:
                dt = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
                stale_timeout = _stale_timeout_for_checkpoint(runtime.get("checkpoint", ""))
                stale = (datetime.now() - dt).total_seconds() > stale_timeout
            except Exception:
                stale = True
        if stale:
            runtime["running"] = False
            runtime["message"] = "Stalled task detected. Ready to resume."
            runtime["checkpoint"] = "stale_detected"

    if len(completed_steps) == 5:
        runtime["progress"] = 100
        runtime["running"] = False
        runtime["checkpoint"] = "done"
        runtime["message"] = "All tasks completed."

    stage_progresses, running_stage = _stage_progresses(experiment, runtime, id)
    dry_available_versions = _available_versions(id, "dry")
    coding_available_versions = _available_versions(id, "coding")
    dry_done_versions = [v for v in [1, 2, 3] if bool(experiment.get(f"page_dry_{v}", False))]
    coding_done_versions = [v for v in [1, 2, 3] if bool(experiment.get(f"page_coding_{v}", False))]

    return {
        "completed_steps": completed_steps,
        "stage_progresses": stage_progresses,
        "running_stage": running_stage,
        "dry_available_versions": dry_available_versions,
        "coding_available_versions": coding_available_versions,
        "dry_done_versions": dry_done_versions,
        "coding_done_versions": coding_done_versions,
        **runtime,
    }
