import uvicorn
from fastapi import FastAPI
from app.routers import experiments

# from fastapi.staticfiles import StaticFiles
# from starlette.responses import FileResponse


app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return {"message": "Hello World"}

app.include_router(experiments.router)
