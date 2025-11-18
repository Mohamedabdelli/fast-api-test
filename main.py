from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello from FastAPI!"}

@app.get("/predict")
def predict(x: int, y: int):
    return {"result": x + y}
