from typing import List, Tuple, Dict, Any, Set
from app.schemas.article import ArticleCreate
from app.utils.text_utils import calculate_title_similarity, normalize_title, normalize_url, compute_content_hash
from app.utils.logger import get_logger

logger = get_logger("news_engine.deduplication_service")

class DuplicatePairInfo:
    def __init__(self, primary_index: int, duplicate_index: int, score: float, method: str):
        self.primary_index = primary_index
        self.duplicate_index = duplicate_index
        self.score = score
        self.method = method

class DeduplicationService:
    """Multi-stage duplicate article detector maintaining duplicate relationships."""

    @staticmethod
    def deduplicate(
        articles: List[ArticleCreate],
        similarity_threshold: float = 0.85
    ) -> Tuple[List[ArticleCreate], List[Dict[str, Any]]]:
        """
        Identify unique primary articles and detected duplicate pairs.
        Returns:
            (unique_articles, duplicate_relationships_data)
        """
        if not articles:
            return [], []

        unique_articles: List[ArticleCreate] = []
        duplicate_records: List[Dict[str, Any]] = []

        seen_urls: Dict[str, int] = {}       # url -> unique_articles index
        seen_titles: Dict[str, int] = {}     # norm_title -> unique_articles index
        seen_hashes: Dict[str, int] = {}     # content_hash -> unique_articles index

        for idx, article in enumerate(articles):
            norm_url = article.canonical_url or normalize_url(article.url)
            norm_title = article.normalized_title or normalize_title(article.title)
            content_hash = article.content_hash or compute_content_hash(article.title, article.description)

            is_dup = False
            primary_idx = None
            method = None
            score = 1.0

            # Stage 1: Exact Canonical / Normalized URL match
            if norm_url and norm_url in seen_urls:
                is_dup = True
                primary_idx = seen_urls[norm_url]
                method = "normalized_url"
                score = 1.0
            # Stage 2: Exact Content Hash match
            elif content_hash and content_hash in seen_hashes:
                is_dup = True
                primary_idx = seen_hashes[content_hash]
                method = "content_hash"
                score = 1.0
            # Stage 3: Exact Normalized Title match
            elif norm_title and norm_title in seen_titles:
                is_dup = True
                primary_idx = seen_titles[norm_title]
                method = "normalized_title"
                score = 1.0
            # Stage 4: Title similarity ratio check
            else:
                for existing_idx, existing in enumerate(unique_articles):
                    existing_norm_t = existing.normalized_title or normalize_title(existing.title)
                    sim = calculate_title_similarity(norm_title, existing_norm_t)
                    if sim >= similarity_threshold:
                        is_dup = True
                        primary_idx = existing_idx
                        method = "title_similarity"
                        score = round(sim, 3)
                        break

            if is_dup and primary_idx is not None:
                primary_article = unique_articles[primary_idx]
                duplicate_records.append({
                    "primary_article_title": primary_article.title,
                    "duplicate_article_title": article.title,
                    "primary_url": primary_article.url,
                    "duplicate_url": article.url,
                    "similarity_score": score,
                    "detection_method": method
                })
                logger.info(f"Duplicate found [{method} score={score}]: '{article.title}' -> Primary '{primary_article.title}'")
            else:
                # Add to unique set
                new_idx = len(unique_articles)
                unique_articles.append(article)
                if norm_url:
                    seen_urls[norm_url] = new_idx
                if norm_title:
                    seen_titles[norm_title] = new_idx
                if content_hash:
                    seen_hashes[content_hash] = new_idx

        return unique_articles, duplicate_records
