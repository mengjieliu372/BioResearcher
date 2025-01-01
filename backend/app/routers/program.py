from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
import os
from app.models.our_utils import read_txt

router = APIRouter()

@router.get("/{id}/program")
async def get_program(id: int, value: int):
    try:
        return process_program(id, value)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory coding not found for experiment id {id}.")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Error decoding the JSON data in the coding file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


def process_program(id: int, value: int):
    # code_dir = Path(__file__).parent.parent / "data" / str(id) / f"coding{value + 1}"
    data_dir = Path(__file__).parent.parent / "data" / str(id)     # 暂时只生成一次代码
    name_dirs = os.listdir(data_dir)
    code_dir = None
    for name in name_dirs:
        if "coding" in name:
            code_dir = data_dir / name
            break
    if not code_dir or not code_dir.exists():
        raise FileNotFoundError(f"Directory not found: {code_dir}")
    files_in_codingdir = os.listdir(code_dir)
    files_Rcode = dict()
    for file in files_in_codingdir:
        if file.endswith('.R') or file.endswith('.r') or file.endswith('.sh'):
            code_path = code_dir / file
            code_txt = read_txt(code_path)
            files_Rcode[file] = code_txt

    return files_Rcode
