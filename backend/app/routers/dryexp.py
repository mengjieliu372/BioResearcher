from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()

@router.get("/{id}/dryexp")
async def get_dryexp(id: int, value: int):
    try:
        return process_dryexp(id, value)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File dry_experiment{value + 1}.json not found for experiment id {id}.")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding the JSON data in dry_experiment{value + 1}.json : {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


def convert_task_fields(data):
    # 需要处理的字段
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
