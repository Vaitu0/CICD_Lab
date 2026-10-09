from fastapi import FastAPI

app=FastAPI()

@app.get("/")
def home():
    return {"message": "Hello World!"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    

