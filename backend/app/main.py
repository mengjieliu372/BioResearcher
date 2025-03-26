import uvicorn
from fastapi import FastAPI
from app.routers import experiments
from app.routers import files
from app.routers import search
from app.routers import dryexp
from app.routers import expdesign
from app.routers import litprocess
from app.routers import program
from app.routers import process

# from fastapi.staticfiles import StaticFiles
# from starlette.responses import FileResponse


app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return {"message": "Hello World"}

app.include_router(experiments.router)

app.include_router(files.router)

app.include_router(search.router)

app.include_router(dryexp.router)

app.include_router(expdesign.router)

app.include_router(litprocess.router)

app.include_router(program.router)

app.include_router(process.router)