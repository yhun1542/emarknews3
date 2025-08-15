from fastapi import FastAPI
import uvicorn
import subprocess

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    subprocess.run(["node", "backend_AI_enhanced.js"])
    uvicorn.run(app, host="0.0.0.0", port=8000)