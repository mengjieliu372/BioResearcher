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
    extra_data_file = Path(__file__).parent.parent / "data" / str(id) / f"experiment_program{value + 1}.log"
    if not data_file.exists() or not extra_data_file.exists():
        raise FileNotFoundError("File not found")
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            expdesign = json.load(f)
        with open(extra_data_file, 'r', encoding='utf-8') as f:
            extra_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError("Error decoding JSON.", "", 0) from e
    extra_data = extra_data["step1"]["json"]
    for key in expdesign.keys():
        if key in extra_data:
            expdesign[key]["Purpose"] = extra_data[key]["Purpose"]
            expdesign[key]["Design Reason"] = extra_data[key]["Design Reason"]
        else:
            # 填充空值
            expdesign[key]["Purpose"] = "Null"
            expdesign[key]["Design Reason"] = "Null"
    return expdesign
