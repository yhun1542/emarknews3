import os
import subprocess
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

# 정적 파일 서빙을 위한 설정
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

def start_node_server():
    """Node.js 서버를 별도 스레드에서 실행"""
    subprocess.run(["node", "server.js"])

if __name__ == "__main__":
    # Node.js 서버를 백그라운드에서 시작
    node_thread = threading.Thread(target=start_node_server, daemon=True)
    node_thread.start()
    
    # Railway에서 제공하는 PORT 환경변수 사용, 기본값은 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

