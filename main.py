import os
import subprocess
import threading
import requests
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙을 위한 설정
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/health")
async def health_check():
    return {"status": "OK"}

@app.get("/api/news")
async def get_news():
    """뉴스 API 엔드포인트"""
    try:
        # 환경변수에서 API 키 가져오기
        gnews_api_key = os.environ.get("GNEWS_API_KEY")
        news_api_key = os.environ.get("NEWS_API_KEY")
        
        news_data = []
        
        # GNews API 호출
        if gnews_api_key:
            try:
                gnews_url = f"https://gnews.io/api/v4/top-headlines?token={gnews_api_key}&lang=ko&country=kr&max=10"
                response = requests.get(gnews_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles'][:5]:
                            news_data.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'image': article.get('image', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'GNews')
                            })
            except Exception as e:
                print(f"GNews API 오류: {e}")
        
        # NewsAPI 호출 (백업)
        if len(news_data) < 5 and news_api_key:
            try:
                newsapi_url = f"https://newsapi.org/v2/top-headlines?country=kr&apiKey={news_api_key}&pageSize=10"
                response = requests.get(newsapi_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles'][:10-len(news_data)]:
                            news_data.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'url': article.get('url', ''),
                                'image': article.get('urlToImage', ''),
                                'publishedAt': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'NewsAPI')
                            })
            except Exception as e:
                print(f"NewsAPI 오류: {e}")
        
        # 샘플 데이터 (API 호출 실패 시)
        if not news_data:
            news_data = [
                {
                    'title': '샘플 뉴스 제목 1',
                    'description': '이것은 샘플 뉴스 설명입니다.',
                    'url': 'https://example.com',
                    'image': '',
                    'publishedAt': '2025-08-15T03:00:00Z',
                    'source': 'Sample News'
                },
                {
                    'title': '샘플 뉴스 제목 2',
                    'description': '두 번째 샘플 뉴스 설명입니다.',
                    'url': 'https://example.com',
                    'image': '',
                    'publishedAt': '2025-08-15T02:30:00Z',
                    'source': 'Sample News'
                }
            ]
        
        return JSONResponse(content=news_data)
        
    except Exception as e:
        print(f"뉴스 API 오류: {e}")
        return JSONResponse(content=[], status_code=500)

def start_node_server():
    """Node.js 서버를 별도 스레드에서 실행 (선택사항)"""
    try:
        subprocess.run(["node", "server.js"])
    except Exception as e:
        print(f"Node.js 서버 시작 실패: {e}")

if __name__ == "__main__":
    # Railway에서 제공하는 PORT 환경변수 사용, 기본값은 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

