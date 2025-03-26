from fastapi import APIRouter
from pathlib import Path
import json

router = APIRouter()

Experiments_File = Path(__file__).parent.parent / "data" / "experiments.json"


@router.get("/{id}/process")
async def get_process(id: int):
    with Experiments_File.open() as f:
        experiments = json.load(f)
    experiment = next((exp for exp in experiments if exp["id"] == id), None)
    if experiment is None:
        return {"message": f"Experiment {id} not found"}
    completed_steps = []
    if experiment['page_search_paper'] and experiment['page_search_datasets']:
        completed_steps.append(0)
    if experiment['page_Literature_processing']:
        completed_steps.append(1)
    if experiment['page_design_1'] and experiment['page_design_2'] and experiment['page_design_3']:
        completed_steps.append(2)
    if experiment['page_dry_1'] and experiment['page_dry_2'] and experiment['page_dry_3']:
        completed_steps.append(3)
    if experiment['page_coding_1'] and experiment['page_coding_2'] and experiment['page_coding_3']:
        completed_steps.append(4)
    return completed_steps
