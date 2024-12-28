import uvicorn
from fastapi import FastAPI

# from fastapi.staticfiles import StaticFiles
# from starlette.responses import FileResponse


app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return {"message": "Hello World"}


if __name__ == "__main__":
    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
