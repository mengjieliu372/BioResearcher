from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os

router = APIRouter()

@router.get("/{id}/expdesign")
async def get_expdesign(id: int, value: int):
    try:
        return process_expdesign(id, value)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File experiment_program{value + 1}.json not found for experiment id {id}.")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding the JSON data in the experiment_program{value + 1}.json file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


def process_expdesign(id: int, value: int):
    data_file = Path(__file__).parent.parent / "data" / str(id) / f"experiment_program{value + 1}.json"
    if not data_file.exists():
        raise FileNotFoundError(f"File not found: {data_file}")
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            expdesign = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError("Error decoding JSON.", "", 0) from e
    return expdesign
