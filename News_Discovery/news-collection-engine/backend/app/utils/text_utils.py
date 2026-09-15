import re
import hashlib
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from difflib import SequenceMatcher

def normalize_title(title: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    if not title:
        return ""
    # Remove HTML tags if present
    clean = re.sub(r'<[^>]+>', '', title)
    # Remove special characters / punctuation
    clean = re.sub(r'[^\w\s]', '', clean.lower())
    # Collapse multiple whitespaces
    return re.sub(r'\s+', ' ', clean).strip()

def normalize_url(url: str) -> str:
    """Strip tracking parameters (utm_*, ref, etc.), normalize scheme & trailing slashes."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Filter out common tracking query params
        ignored_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'ref', 'source', 'gclid', 'fbclid'}
        query_pairs = parse_qsl(parsed.query)
        filtered_query = [(k, v) for k, v in query_pairs if k.lower() not in ignored_params]
        clean_query = urlencode(filtered_query)
        
        # Scheme to lower, netloc to lower
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip('/') if parsed.path != '/' else '/'
        
        return urlunparse((scheme, netloc, path, parsed.params, clean_query, ''))
    except Exception:
        return url.strip().rstrip('/')

def compute_content_hash(title: str, description: str = None) -> str:
    """Generate MD5 hash of normalized title and description."""
    norm_t = normalize_title(title)
    norm_d = normalize_title(description or "")
    combined = f"{norm_t}|{norm_d}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()

def calculate_title_similarity(title1: str, title2: str) -> float:
    """Calculate SequenceMatcher similarity score between two normalized titles."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return 0.0
    return SequenceMatcher(None, norm1, norm2).ratio()

def compute_dedup_hash(title: str, published_at: str = None) -> str:
    """Generate SHA256/MD5 hash of normalized title + published date for story deduplication across sources."""
    norm_t = normalize_title(title)
    pub_date_str = ""
    if published_at:
        try:
            pub_date_str = str(published_at)[:10]  # YYYY-MM-DD
        except Exception:
            pub_date_str = ""
    combined = f"{norm_t}:{pub_date_str}"
    return hashlib.md5(combined.encode('utf-8')).hexdigest()
