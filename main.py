import os
import subprocess
import threading
import requests
import json
import random
from datetime import datetime
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

def translate_text(text, target_lang='ko'):
    """OpenAI API를 사용한 번역"""
    try:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return text
            
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a professional translator. Translate the given text to Korean naturally and accurately."},
                {"role": "user", "content": f"Translate this to Korean: {text}"}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"번역 오류: {e}")
    
    return text

def generate_summary(text):
    """OpenAI API를 사용한 요약"""
    try:
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return text[:100] + "..."
            
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a news summarizer. Create a concise Korean summary in 1-2 sentences."},
                {"role": "user", "content": f"Summarize this news in Korean: {text}"}
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post("https://api.openai.com/v1/chat/completions", 
                               headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"요약 오류: {e}")
    
    return text[:100] + "..."

def calculate_rating(title, description):
    """뉴스 품질 평점 계산 (0.5 단위)"""
    score = 3.0  # 기본 점수
    
    # 제목 길이 평가
    if len(title) > 10:
        score += 0.5
    if len(title) > 30:
        score += 0.5
        
    # 설명 길이 평가
    if len(description) > 50:
        score += 0.5
    if len(description) > 100:
        score += 0.5
        
    # 키워드 기반 평가
    important_keywords = ['경제', '정치', '기술', '사회', '국제', '문화', '스포츠']
    for keyword in important_keywords:
        if keyword in title or keyword in description:
            score += 0.5
            break
    
    # 0.5 단위로 반올림, 1.0-5.0 범위
    score = round(score * 2) / 2
    return max(1.0, min(5.0, score))

def generate_tags(title, description):
    """뉴스 태그 생성"""
    tags = []
    
    # 카테고리 태그
    if any(word in title + description for word in ['경제', '금융', '주식', '투자']):
        tags.append('경제')
    if any(word in title + description for word in ['정치', '정부', '국회', '선거']):
        tags.append('정치')
    if any(word in title + description for word in ['기술', 'IT', '인공지능', 'AI']):
        tags.append('기술')
    if any(word in title + description for word in ['사회', '사건', '사고']):
        tags.append('사회')
    if any(word in title + description for word in ['국제', '해외', '글로벌']):
        tags.append('국제')
    if any(word in title + description for word in ['문화', '예술', '엔터']):
        tags.append('문화')
    if any(word in title + description for word in ['스포츠', '축구', '야구']):
        tags.append('스포츠')
    
    # 기본 태그가 없으면 '일반' 추가
    if not tags:
        tags.append('일반')
    
    return tags

@app.get("/api/news")
async def get_news():
    """향상된 뉴스 API 엔드포인트"""
    try:
        # 환경변수에서 API 키 가져오기
        gnews_api_key = os.environ.get("GNEWS_API_KEY")
        news_api_key = os.environ.get("NEWS_API_KEY")
        naver_client_id = os.environ.get("NAVER_CLIENT_ID")
        naver_client_secret = os.environ.get("NAVER_CLIENT_SECRET")
        youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
        
        news_data = []
        
        # 1. GNews API 호출
        if gnews_api_key and gnews_api_key != "placeholder":
            try:
                gnews_url = f"https://gnews.io/api/v4/top-headlines?token={gnews_api_key}&lang=ko&country=kr&max=5"
                response = requests.get(gnews_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles']:
                            title_ko = translate_text(article.get('title', ''))
                            description_ko = generate_summary(article.get('description', ''))
                            rating = calculate_rating(title_ko, description_ko)
                            tags = generate_tags(title_ko, description_ko)
                            
                            news_data.append({
                                'title_en': article.get('title', ''),
                                'title_ko': title_ko,
                                'summary': description_ko,
                                'url': article.get('url', ''),
                                'image': article.get('image', ''),
                                'published': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'GNews'),
                                'rating': rating,
                                'tags': tags
                            })
            except Exception as e:
                print(f"GNews API 오류: {e}")
        
        # 2. NewsAPI 호출 (백업)
        if len(news_data) < 5 and news_api_key and news_api_key != "placeholder":
            try:
                newsapi_url = f"https://newsapi.org/v2/top-headlines?country=kr&apiKey={news_api_key}&pageSize=5"
                response = requests.get(newsapi_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'articles' in data:
                        for article in data['articles']:
                            title_ko = translate_text(article.get('title', ''))
                            description_ko = generate_summary(article.get('description', ''))
                            rating = calculate_rating(title_ko, description_ko)
                            tags = generate_tags(title_ko, description_ko)
                            
                            news_data.append({
                                'title_en': article.get('title', ''),
                                'title_ko': title_ko,
                                'summary': description_ko,
                                'url': article.get('url', ''),
                                'image': article.get('urlToImage', ''),
                                'published': article.get('publishedAt', ''),
                                'source': article.get('source', {}).get('name', 'NewsAPI'),
                                'rating': rating,
                                'tags': tags
                            })
            except Exception as e:
                print(f"NewsAPI 오류: {e}")
        
        # 3. Naver 뉴스 API 호출
        if len(news_data) < 5 and naver_client_id and naver_client_secret:
            try:
                headers = {
                    'X-Naver-Client-Id': naver_client_id,
                    'X-Naver-Client-Secret': naver_client_secret
                }
                naver_url = "https://openapi.naver.com/v1/search/news.json?query=뉴스&display=5&sort=date"
                response = requests.get(naver_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'items' in data:
                        for item in data['items']:
                            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
                            description = item.get('description', '').replace('<b>', '').replace('</b>', '')
                            rating = calculate_rating(title, description)
                            tags = generate_tags(title, description)
                            
                            news_data.append({
                                'title_en': title,
                                'title_ko': title,
                                'summary': description,
                                'url': item.get('link', ''),
                                'image': '',
                                'published': item.get('pubDate', ''),
                                'source': 'Naver News',
                                'rating': rating,
                                'tags': tags
                            })
            except Exception as e:
                print(f"Naver API 오류: {e}")
        
        # 4. 샘플 데이터 (모든 API 실패 시)
        if not news_data:
            sample_news = [
                {
                    'title_en': 'Breaking: Major Economic Development',
                    'title_ko': '속보: 주요 경제 발전',
                    'summary': '경제 분야에서 중요한 발전이 있었습니다. 이는 시장에 큰 영향을 미칠 것으로 예상됩니다.',
                    'url': 'https://example.com/news1',
                    'image': '',
                    'published': datetime.now().isoformat(),
                    'source': 'Sample News',
                    'rating': 4.5,
                    'tags': ['경제', '속보']
                },
                {
                    'title_en': 'Technology Innovation Breakthrough',
                    'title_ko': '기술 혁신의 돌파구',
                    'summary': '최신 기술 혁신이 발표되었습니다. 이 기술은 미래를 바꿀 잠재력을 가지고 있습니다.',
                    'url': 'https://example.com/news2',
                    'image': '',
                    'published': datetime.now().isoformat(),
                    'source': 'Sample News',
                    'rating': 4.0,
                    'tags': ['기술', '혁신']
                },
                {
                    'title_en': 'Global Political Update',
                    'title_ko': '글로벌 정치 업데이트',
                    'summary': '국제 정치 상황에 새로운 변화가 있었습니다. 각국의 반응이 주목됩니다.',
                    'url': 'https://example.com/news3',
                    'image': '',
                    'published': datetime.now().isoformat(),
                    'source': 'Sample News',
                    'rating': 3.5,
                    'tags': ['정치', '국제']
                }
            ]
            news_data = sample_news
        
        # sum_limit=10 필터 적용
        news_data = news_data[:10]
        
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
    # Railway에서 제공하는 PORT 환경변수 사용
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

