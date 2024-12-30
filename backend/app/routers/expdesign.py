from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

@router.get("/{id}/expdesign")
async def get_expdesign(id:int, value: int):
    return process_expdesign(id, value)

def process_expdesign(id: int, value: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id) / f"experiment_program{value + 1}.json"
    with open(DataFile, 'r', encoding='utf-8') as f:
        expdesign = json.load(f)
    return expdesign
