from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json
import random


router = APIRouter()


Experiments_File = Path(__file__).parent.parent / "data" / "experiments.json"
existing_ids = set()


class PaperSet(BaseModel):
    PMC: bool
    PubMed: bool

class Dataset(BaseModel):
    GEO: bool
    NCBI: bool
    cBioPortal: bool

class Experiment(BaseModel):
    expName: str
    expPurpose: str
    expCondition: str
    expRequirement: str
    paperset: PaperSet
    dataset: Dataset
    llmModel: str
    refNum: Optional[int] = None
    reviewerRound: Optional[int] = None



@router.post("/addExperiment")
async def add_experiment(experiment: Experiment):
    try:
        experiment_dict = experiment.model_dump()
        experiment_dict["id"] = generate_id()
        experiments = read_experiments()
        experiments.append(experiment_dict)
        write_experiments(experiments)
        return {"message": "Experiment added successfully"}
    except Exception as e:
        return {"error": str(e)}

@router.get("/getExperiments")
async def get_experiments():
    try:
        experiments = read_experiments()
        return experiments
    except Exception as e:
        return {"error": str(e)}


def read_experiments():
    with open(Experiments_File, "r") as f:
        json_data = json.load(f)
        # get the existing ids
        for item in json_data:
            existing_ids.add(item["id"])
        return json_data


def write_experiments(experiments):
    with open(Experiments_File, "w") as f:
        json.dump(experiments, f, indent=4)


def generate_id():
    while True:
        new_id = random.randint(10000, 99999)
        if new_id not in existing_ids:
            existing_ids.add(new_id)
            return new_id

@router.post("/uploadfile")
async def upload_file():
    return {"message": "Upload file here"}
