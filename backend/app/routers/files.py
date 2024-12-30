from fastapi import APIRouter, UploadFile, File
from pathlib import Path

router = APIRouter()

PDF_Folder = Path(__file__).parent.parent / "data" / "pdfs"

@router.post("/uploadfile")
async def create_upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    with open(PDF_Folder / file.filename, "wb") as f:
        f.write(contents)
    return {"filename": file.filename}


# 删除文件
@router.delete("/deletefile")
async def delete_file(file_name: str):
    file_path = PDF_Folder / file_name
    print(file_path)
    if file_path.exists():
        file_path.unlink()
        return {"message": "File deleted"}
    return {"message": "File not found"}
