const express = require('express');
const axios = require('axios');
const { GoogleCloudTranslation } = require('@google-cloud/translate');
const app = express();
const port = 3000;

const NAVER_API = 'https://openapi.naver.com/v1/search/news.json';
const NEWSAPI = 'https://newsapi.org/v2/top-headlines';
const YOUTUBE_API = 'https://www.googleapis.com/youtube/v3/search';
const TRANSLATE = new GoogleCloudTranslation();

app.use(express.json());

app.get('/api/news', async (req, res) => {
    try {
        const [naverRes, newsRes, ytRes] = await Promise.all([
            axios.get(NAVER_API, { headers: { 'X-Naver-Client-Id': process.env.NAVER_API_KEY }, params: { query: 'AI' } }),
            axios.get(NEWSAPI, { headers: { 'Authorization': process.env.NEWSAPI_KEY }, params: { q: 'AI' } }),
            axios.get(YOUTUBE_API, { params: { key: process.env.YOUTUBE_API_KEY, q: 'AI news' } })
        ]);

        const articles = [];
        naverRes.data.items.forEach(item => {
            articles.push({ title_en: item.title, source: 'Naver', published: item.pubDate, tags: ['news'], rating: 4.5 });
        });
        newsRes.data.articles.forEach(item => {
            articles.push({ title_en: item.title, source: 'NewsAPI', published: item.publishedAt, tags: ['global'], rating: 4.0 });
        });
        ytRes.data.items.forEach(item => {
            articles.push({ title_en: item.snippet.title, source: 'YouTube', published: item.snippet.publishedAt, tags: ['video'], rating: 4.2 });
        });

        const sum_limit = 10;
        const summaries = await Promise.all(articles.slice(0, sum_limit).map(async item => {
            const translated = await TRANSLATE.translate(item.title_en, 'ko');
            const summary = item.title_en.slice(0, 100); // AI 요약 대신 단순화
            return { ...item, title_ko: translated[0], summary };
        }));

        res.set('ETag', Date.now().toString());
        res.json(summaries);
    } catch (error) {
        res.status(500).send('Server Error');
    }
});

app.listen(port, () => console.log(`Backend running on port ${port}`));