from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

@router.get("/{id}/dryexp")
async def get_dryexp(id:int, value: int):
    return process_dryexp(id, value)

def process_dryexp(id: int, value: int):
    DataFile = Path(__file__).parent.parent / "data" / str(id) / f"dry_experiment{value + 1}.json"
    with open(DataFile, 'r', encoding='utf-8') as f:
        dryexp = json.load(f)
    return dryexp