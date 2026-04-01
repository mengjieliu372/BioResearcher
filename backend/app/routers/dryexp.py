from fastapi import APIRouter, HTTPException, Header
from pathlib import Path
import json
from app.auth_core import ensure_project_access, require_user

router = APIRouter()

@router.get("/{id}/dryexp")
async def get_dryexp(id: int, value: int, authorization: str | None = Header(default=None)):
    user = require_user(authorization)
    ensure_project_access(user, id)
    try:
        return combine_code(id, value)
    except FileNotFoundError:
        data_dir = Path(__file__).parent.parent / "data" / str(id)
        available = []
        if data_dir.exists():
            for p in data_dir.glob("dry_experiment*.json"):
                digits = "".join(ch for ch in p.stem if ch.isdigit())
                if digits:
                    available.append(int(digits))
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"File dry_experiment{value + 1}.json not found for experiment id {id}.",
                "available_versions": sorted(set(available)),
            },
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding the JSON data in dry_experiment{value + 1}.json : {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

def combine_code(id, value):
    ori_data = process_dryexp(id, value)
    if value != 2:
        return ori_data
    # For version 3, attach generated code if present. Do not fail hard on missing code files.
    for part_name, tasks in ori_data.items():
        for task in tasks:
            task_id = task.get("task_id").replace(" ", "")
            code_file = Path(__file__).parent.parent / "data" / str(id) / "coding3" / f"{task_id}-1.r"
            if code_file.exists():
                with open(code_file, 'r', encoding='utf-8') as f:
                    code_text = f.read()
                task["code"] = code_text
            else:
                task["code"] = ""
    return ori_data


def convert_task_fields(data):
    # 闂団偓鐟曚礁顦╅悶鍡欐畱鐎涙顔?
    task_fields = ["task_id", "task_description", "input", "output"]
    if isinstance(data, dict):
        return {
            key: convert_task_fields(value) if key not in task_fields else str(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [convert_task_fields(item) for item in data]
    else:
        return data

def process_dryexp(id: int, value: int):
    data_file = Path(__file__).parent.parent / "data" / str(id) / f"dry_experiment{value + 1}.json"
    if not data_file.exists():
        raise FileNotFoundError(f"File not found: {data_file}")
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            dryexp = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError("Error decoding JSON.", "", 0) from e
    return convert_task_fields(dryexp)
