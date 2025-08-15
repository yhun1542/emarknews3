const express = require('express');
const axios = require('axios');
const { Translate } = require('@google-cloud/translate').v2;
const app = express();

// Railway에서 제공하는 PORT 환경변수 사용, 기본값은 3001
const port = process.env.NODE_PORT || 3001;

const NAVER_API = 'https://openapi.naver.com/v1/search/news.json';
const NEWSAPI = 'https://newsapi.org/v2/top-headlines';
const YOUTUBE_API = 'https://www.googleapis.com/youtube/v3/search';

// Google Translate 초기화 (환경변수가 있을 때만)
let translate = null;
if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    translate = new Translate();
}

app.use(express.json());
app.use(express.static('.'));

// CORS 설정
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    next();
});

app.get('/api/news', async (req, res) => {
    try {
        const articles = [];
        
        // 기본 뉴스 데이터 (API 키가 없어도 작동하도록)
        const sampleNews = [
            {
                title_en: "AI Technology Advances in 2024",
                title_ko: "2024년 AI 기술 발전",
                source: "Tech News",
                published: new Date().toISOString(),
                tags: ["AI", "Technology"],
                rating: 4.5,
                summary: "Latest developments in artificial intelligence technology..."
            },
            {
                title_en: "Machine Learning Breakthrough",
                title_ko: "머신러닝 혁신",
                source: "Science Daily",
                published: new Date().toISOString(),
                tags: ["ML", "Research"],
                rating: 4.2,
                summary: "New machine learning algorithms show promising results..."
            },
            {
                title_en: "Future of Automation",
                title_ko: "자동화의 미래",
                source: "Future Tech",
                published: new Date().toISOString(),
                tags: ["Automation", "Future"],
                rating: 4.0,
                summary: "How automation will change industries in the coming years..."
            }
        ];

        // API 키가 있으면 실제 API 호출, 없으면 샘플 데이터 사용
        if (process.env.NEWSAPI_KEY) {
            try {
                const newsRes = await axios.get(NEWSAPI, {
                    headers: { 'Authorization': `Bearer ${process.env.NEWSAPI_KEY}` },
                    params: { q: 'AI technology', language: 'en', pageSize: 5 }
                });
                
                newsRes.data.articles.forEach(item => {
                    articles.push({
                        title_en: item.title,
                        title_ko: item.title, // 번역 API가 없으면 원문 사용
                        source: item.source.name,
                        published: item.publishedAt,
                        tags: ['news'],
                        rating: 4.0,
                        summary: item.description || item.title.slice(0, 100)
                    });
                });
            } catch (apiError) {
                console.log('API 호출 실패, 샘플 데이터 사용:', apiError.message);
                articles.push(...sampleNews);
            }
        } else {
            console.log('API 키가 없어 샘플 데이터 사용');
            articles.push(...sampleNews);
        }

        // 번역 처리 (Google Translate API가 있을 때만)
        if (translate && articles.length > 0) {
            try {
                for (let article of articles) {
                    if (article.title_en === article.title_ko) {
                        const [translation] = await translate.translate(article.title_en, 'ko');
                        article.title_ko = translation;
                    }
                }
            } catch (translateError) {
                console.log('번역 실패:', translateError.message);
            }
        }

        res.set('ETag', Date.now().toString());
        res.json(articles.slice(0, 10)); // 최대 10개 항목 반환
    } catch (error) {
        console.error('서버 오류:', error);
        res.status(500).json({ error: 'Server Error', message: error.message });
    }
});

app.get('/health', (req, res) => {
    res.json({ status: 'OK', port: port });
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Node.js 백엔드 서버가 포트 ${port}에서 실행 중입니다.`);
});

