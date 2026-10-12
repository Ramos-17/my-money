from fastapi import FastAPI
from fastapi_back import auth
from fastapi_back.auth import router as auth_router

app = FastAPI()

app.include_router(auth.router)


@app.get("/")
async def root():
    return{"message": "Hello World"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}