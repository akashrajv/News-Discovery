from datetime import datetime, timedelta
from typing import List
from app.schemas.article import ArticleCreate
from app.utils.text_utils import normalize_url, normalize_title, compute_content_hash
from app.services.relevance_service import RelevanceService

def get_demo_articles(entity: str, keywords: List[str]) -> List[ArticleCreate]:
    """
    Generate deterministic mock test articles supporting multiple companies
    (Tata Motors, NVIDIA, Tesla, Apple, Microsoft) with deliberate duplicates.
    """
    now = datetime.utcnow()

    raw_demo_items = [
        # Tata Motors articles
        {
            "title": "Tata Motors announces new electric vehicle platform for global markets",
            "description": "Tata Motors has unveiled its next-generation EV architecture aimed at boosting electric car adoption in India and international markets.",
            "content": "Tata Motors today announced a strategic EV expansion plan involving new modular skateboard architectures...",
            "source": "NewsAPI (Simulated)",
            "published_at": now - timedelta(minutes=15),
            "url": "https://example-newsapi.com/tata-motors-new-ev-platform-2026",
            "category": "Automotive",
            "location": "India",
            "collection_method": "api",
            "source_id": "src_newsapi"
        },
        {
            "title": "Tata Motors announces new electric vehicle platform for global markets",
            "description": "Tata Motors has unveiled its next-generation EV architecture aimed at boosting electric car adoption in India.",
            "content": "Tata Motors today announced a strategic EV expansion plan...",
            "source": "Google News RSS",
            "published_at": now - timedelta(minutes=18),
            "url": "https://news.google.com/articles/tata-motors-new-ev-platform-2026?utm_source=rss",
            "category": "Automotive",
            "location": "India",
            "collection_method": "rss",
            "source_id": "src_rss_google_news"
        },
        {
            "title": "Tata Nexon EV receives battery range upgrade and new feature package",
            "description": "The popular Tata Nexon EV gets an enhanced 45kWh battery pack offering up to 489km range on a single charge.",
            "content": "Tata Motors has updated its best-selling electric SUV with upgraded battery chemistry...",
            "source": "Auto Express RSS",
            "published_at": now - timedelta(minutes=5),
            "url": "https://www.autoexpress.co.uk/tata/nexon-ev-2026-upgrade",
            "category": "Automotive",
            "location": "India",
            "collection_method": "rss",
            "source_id": "src_rss_auto_express"
        },
        {
            "title": "Global automotive industry accelerates shift toward electric vehicle fleets",
            "description": "BBC News reports on accelerating EV adoption and battery technology investments by major automakers worldwide.",
            "content": "Major automakers including Tata Motors, Tesla, and traditional OEMs are expanding global EV production capacity...",
            "source": "BBC News RSS",
            "published_at": now - timedelta(minutes=7),
            "url": "http://feeds.bbci.co.uk/news/articles/global-ev-expansion-2026",
            "category": "Technology",
            "location": "Global",
            "collection_method": "rss",
            "source_id": "src_rss_bbc_news"
        },

        # NVIDIA articles
        {
            "title": "NVIDIA unveils next-generation Blackwell Ultra AI GPU architecture",
            "description": "NVIDIA expands its AI chip lineup with new Blackwell Ultra GPUs delivering 3x throughput for enterprise AI clusters.",
            "content": "At GTC conference, NVIDIA CEO announced new hardware systems optimized for trillion-parameter LLM training...",
            "source": "NewsAPI (Simulated)",
            "published_at": now - timedelta(minutes=10),
            "url": "https://tech-news.com/nvidia-blackwell-ultra-gpu-announcement",
            "category": "Technology",
            "location": "Global",
            "collection_method": "api",
            "source_id": "src_newsapi"
        },
        {
            "title": "NVIDIA unveils next-generation Blackwell Ultra AI GPU architecture",
            "description": "NVIDIA expands its AI chip lineup with new Blackwell Ultra GPUs delivering 3x throughput.",
            "content": "NVIDIA CEO announced new hardware systems optimized for AI...",
            "source": "Google News RSS",
            "published_at": now - timedelta(minutes=12),
            "url": "https://news.google.com/articles/nvidia-blackwell-ultra?ref=rss",
            "category": "Technology",
            "location": "Global",
            "collection_method": "rss",
            "source_id": "src_rss_google_news"
        },
        {
            "title": "NVIDIA quarterly data center revenue reaches record $30 billion",
            "description": "Hyper-scaler AI spending drives record quarterly earnings for NVIDIA across data center and networking divisions.",
            "content": "NVIDIA reported quarterly revenue growth exceeding Wall Street forecasts...",
            "source": "NewsData.io (Simulated)",
            "published_at": now - timedelta(minutes=25),
            "url": "https://newsdata.io/read/nvidia-q3-earnings-record",
            "category": "Technology",
            "location": "Global",
            "collection_method": "api",
            "source_id": "src_newsdata"
        },

        # Tesla articles
        {
            "title": "Tesla expands Robotaxi trial fleet with new autonomous Cybercab deployment",
            "description": "Tesla has deployed an expanded fleet of autonomous Cybercab vehicles for closed-loop urban testing.",
            "content": "Tesla announced new software releases for full self-driving capabilities...",
            "source": "NewsAPI (Simulated)",
            "published_at": now - timedelta(minutes=14),
            "url": "https://ev-insider.com/tesla-robotaxi-cybercab-deployment",
            "category": "Automotive",
            "location": "US",
            "collection_method": "api",
            "source_id": "src_newsapi"
        },

        # Apple articles
        {
            "title": "Apple Intelligence features roll out to global iPhone and Mac users",
            "description": "Apple launches new generative AI features across iOS and macOS with privacy-first on-device processing.",
            "content": "Apple today announced the general availability of Apple Intelligence suite...",
            "source": "TechCrunch RSS",
            "published_at": now - timedelta(minutes=30),
            "url": "https://techcrunch.com/apple-intelligence-global-launch-2026",
            "category": "Technology",
            "location": "Global",
            "collection_method": "rss",
            "source_id": "src_rss_techcrunch"
        },

        # Microsoft articles
        {
            "title": "Microsoft Azure reports 35% cloud revenue surge powered by Copilot adoption",
            "description": "Microsoft Q3 financial results show strong cloud expansion as enterprise Copilot subscriptions accelerate.",
            "content": "Microsoft Corporation posted quarterly revenue exceeding analyst expectations...",
            "source": "Reuters RSS",
            "published_at": now - timedelta(minutes=45),
            "url": "https://reuters.com/business/microsoft-azure-q3-cloud-revenue-2026",
            "category": "Technology",
            "location": "Global",
            "collection_method": "rss",
            "source_id": "src_rss_reuters"
        }
    ]

    articles = []
    norm_target = (entity or "").strip().lower()

    for item in raw_demo_items:
        # Match company if specific entity requested
        if norm_target and norm_target not in ["all", "*", ""] and "all" not in norm_target:
            target_tokens = [t.strip().lower() for t in norm_target.split(",") if t.strip()]
            item_text = f"{item['title']} {item['description']} {item['content']}".lower()
            if not any(token in item_text for token in target_tokens):
                continue

        analysis = RelevanceService.compute_semantic_analysis(
            title=item["title"],
            description=item["description"],
            content=item["content"],
            target_entity=entity or "All Companies"
        )

        norm_u = normalize_url(item["url"])
        norm_t = normalize_title(item["title"])
        c_hash = compute_content_hash(item["title"], item["description"])

        article = ArticleCreate(
            title=item["title"],
            description=item["description"],
            content=item["content"],
            source=item["source"],
            published_at=item["published_at"],
            url=item["url"],
            category=item["category"],
            location=item["location"],
            collection_method=item["collection_method"],
            canonical_url=norm_u,
            normalized_title=norm_t,
            content_hash=c_hash,
            source_id=item["source_id"],
            publication_time_unavailable=False,
            target_entity=analysis["target_entity"],
            relevance_score=analysis["relevance_score"],
            importance_score=analysis["importance_score"],
            importance_rating=analysis["importance_rating"],
            sentiment_tone=analysis["sentiment_tone"],
            ai_summary=analysis["ai_summary"]
        )
        articles.append(article)

    return articles
