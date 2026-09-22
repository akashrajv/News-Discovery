import re
from typing import Dict, Any, List, Tuple
from app.services.deepseek_service import deepseek_service_instance

class RelevanceService:
    """
    AI-Powered Semantic Discovery & Importance Intelligence Engine.
    Analyzes target company relevance, business importance ratings, impact sentiment,
    and generates AI executive summaries for collected news articles.
    """

    # Knowledge dictionary for target company entities, aliases, products, leaders, and tickers
    COMPANY_KNOWLEDGE = {
        "nvidia": {
            "name": "NVIDIA",
            "tickers": ["NVDA"],
            "aliases": ["nvidia", "nvda", "geforce", "rtx", "blackwell", "hopper", "cuda", "grace hopper", "jensen huang", "dgx", "h100", "h200", "b200"],
            "core_terms": ["gpu", "ai chip", "data center", "artificial intelligence", "semiconductor", "graphics card", "deep learning", "supercomputer"]
        },
        "tata motors": {
            "name": "Tata Motors",
            "tickers": ["TATAMOTORS", "TTM"],
            "aliases": ["tata motors", "tata motor", "tata nexon", "tata tiago", "tata punch", "tata curvv", "tata avinya", "jlr", "jaguar land rover", "tata ev", "tiramisu"],
            "core_terms": ["electric vehicle", "ev", "commercial vehicle", "automaker", "suv", "car sales", "passenger vehicle", "auto industry"]
        },
        "tesla": {
            "name": "Tesla",
            "tickers": ["TSLA"],
            "aliases": ["tesla", "tsla", "elon musk", "cybertruck", "model 3", "model y", "model s", "model x", "megapack", "full self driving", "fsd", "robotaxi", "cybercab"],
            "core_terms": ["electric vehicle", "ev", "supercharger", "gigafactory", "battery", "autonomous driving", "autopilot", "energy storage"]
        },
        "apple": {
            "name": "Apple",
            "tickers": ["AAPL"],
            "aliases": ["apple", "aapl", "iphone", "macbook", "ipad", "apple watch", "airpods", "vision pro", "tim cook", "ios", "macos", "app store", "apple intelligence"],
            "core_terms": ["smartphone", "consumer electronics", "tech giant", "services", "silicon", "m3", "m4", "app ecosystem"]
        },
        "microsoft": {
            "name": "Microsoft",
            "tickers": ["MSFT"],
            "aliases": ["microsoft", "msft", "satya nadella", "azure", "copilot", "windows", "xbox", "surface", "office 365", "teams", "activision", "openai partnership"],
            "core_terms": ["cloud computing", "enterprise software", "ai cloud", "tech giant", "generative ai", "productivity suite"]
        },
        "openai": {
            "name": "OpenAI",
            "tickers": [],
            "aliases": ["openai", "open ai", "chatgpt", "sam altman", "gpt-4", "gpt-5", "sora", "dall-e"],
            "core_terms": ["artificial intelligence", "large language model", "llm", "generative ai", "ai model", "ai agent"]
        },
        "google": {
            "name": "Google",
            "tickers": ["GOOGL", "GOOG"],
            "aliases": ["google", "alphabet", "sundar pichai", "gemini", "deepmind", "android", "chrome", "pixel"],
            "core_terms": ["search engine", "cloud computing", "generative ai", "tech giant", "machine learning"]
        }
    }

    # Strategic business keywords that signify HIGH or CRITICAL business importance
    CRITICAL_IMPORTANCE_KEYWORDS = [
        "acquisition", "merger", "buyout", "earnings report", "quarterly revenue",
        "lawsuit", "sec investigation", "recalls", "reorganisation", "bankruptcy",
        "fda approval", "regulatory approval", "sanctions", "ceo steps down",
        "layoffs", "data breach", "antitrust", "patent dispute"
    ]

    HIGH_IMPORTANCE_KEYWORDS = [
        "unveils", "announces", "launches", "expansion", "partnership", "joint venture",
        "upgrade", "breakthrough", "record sales", "forecast", "dividend", "investment",
        "factory", "gigafactory", "architecture", "next-generation"
    ]

    # Sentiment & Impact indicators
    POSITIVE_IMPACT_KEYWORDS = ["record", "surge", "growth", "breakthrough", "expansion", "unveils", "profit", "upgrade", "success", "leader", "win"]
    RISK_THREAT_KEYWORDS = ["lawsuit", "investigation", "decline", "fall", "penalty", "breach", "drop", "recall", "threat", "delay", "loss", "warning", "ban"]

    @classmethod
    def get_company_context(cls, entity: str) -> Dict[str, Any]:
        """Lookup or generate dynamic semantic dictionary for a target company."""
        if not entity:
            return {"name": "All Companies", "aliases": [], "core_terms": []}

        entity_clean = entity.strip().lower()
        norm_entity = entity_clean.replace(" ", "")

        # 1. Exact or normalized knowledge match
        for key, knowledge in cls.COMPANY_KNOWLEDGE.items():
            norm_key = key.replace(" ", "")
            if norm_key == norm_entity or any(norm_entity == a.replace(" ", "") for a in knowledge.get("aliases", [])):
                return knowledge
            if norm_key in norm_entity or norm_entity in norm_key:
                return knowledge

        # 2. Dynamic fallback for custom company names
        # Avoid common generic stopwords from becoming standalone aliases
        COMMON_STOPWORDS = {"the", "and", "inc", "corp", "ltd", "llc", "group", "co", "open", "house", "new", "global", "international"}
        words = [w for w in re.findall(r'\b\w+\b', entity_clean) if len(w) >= 3 and w not in COMMON_STOPWORDS]
        aliases = [entity_clean]
        if "technologies" in entity_clean:
            aliases.append(entity_clean.replace("technologies", "tech").strip())
        elif "tech" in entity_clean:
            aliases.append(entity_clean.replace("tech", "technologies").strip())
        if norm_entity != entity_clean and len(norm_entity) >= 3 and norm_entity not in COMMON_STOPWORDS:
            aliases.append(norm_entity)

        return {
            "name": entity.strip(),
            "aliases": list(dict.fromkeys(aliases)),
            "core_terms": words if words else [entity_clean]
        }

    @classmethod
    def compute_semantic_analysis(
        cls,
        title: str,
        description: str = None,
        content: str = None,
        target_entity: str = "All Companies",
        keywords: Any = None
    ) -> Dict[str, Any]:
        """
        Calculates Target Relevance Score (0-100%), Business Importance Rating (CRITICAL, HIGH, MEDIUM, LOW),
        Impact Sentiment, and generates an AI importance summary.
        Scoring is strictly based on the target company and given keywords.
        """
        title_text = (title or "").strip()
        desc_text = (description or "").strip()
        body_text = (content or "").strip()
        full_text = f"{title_text} {desc_text} {body_text}".lower()
        title_lower = title_text.lower()

        # Parse user keywords if provided (list or comma-separated string)
        parsed_keywords: List[str] = []
        if isinstance(keywords, list):
            parsed_keywords = [str(k).strip().lower() for k in keywords if str(k).strip()]
        elif isinstance(keywords, str) and keywords.strip():
            parsed_keywords = [k.strip().lower() for k in keywords.split(",") if k.strip()]

        # Parse target entities (supports single or comma-separated targets)
        if not target_entity or target_entity.strip().lower() in ["all", "all companies"]:
            target_entities_list = list(cls.COMPANY_KNOWLEDGE.keys())
        else:
            target_entities_list = [e.strip() for e in target_entity.split(",") if e.strip()]

        if len(target_entities_list) > 1:
            best_analysis = None
            max_relevance = -1.0
            for single_target in target_entities_list:
                analysis = cls._compute_single_entity_analysis(
                    title_text, desc_text, body_text, full_text, title_lower, single_target, parsed_keywords
                )
                if analysis["relevance_score"] > max_relevance:
                    max_relevance = analysis["relevance_score"]
                    best_analysis = analysis
            return best_analysis or cls._compute_single_entity_analysis(
                title_text, desc_text, body_text, full_text, title_lower, target_entities_list[0], parsed_keywords
            )
        else:
            single_target = target_entities_list[0] if target_entities_list else "All Companies"
            return cls._compute_single_entity_analysis(
                title_text, desc_text, body_text, full_text, title_lower, single_target, parsed_keywords
            )

    @classmethod
    def _compute_single_entity_analysis(
        cls,
        title_text: str,
        desc_text: str,
        body_text: str,
        full_text: str,
        title_lower: str,
        target_entity: str,
        keywords: List[str] = None
    ) -> Dict[str, Any]:
        context = cls.get_company_context(target_entity)
        aliases = context.get("aliases", [])
        core_terms = context.get("core_terms", [])
        company_name = context.get("name", target_entity or "Target Company")
        keywords = keywords or []

        # 1. Target Relevance Score Calculation (0 - 100%)
        # Strictly calculated based ONLY on:
        # (A) Target Company Given (name, ticker, aliases in title/body)
        # (B) Keywords of the Target Company Given (user keywords and/or domain core terms in title/body)
        company_score = 0.0
        keyword_score = 0.0

        def has_term(term: str, text: str) -> bool:
            if not term or not text:
                return False
            escaped = re.escape(term.lower().strip())
            pattern = rf"(?<!\w){escaped}(?!\w)"
            return bool(re.search(pattern, text))

        def count_term(term: str, text: str) -> int:
            if not term or not text:
                return 0
            escaped = re.escape(term.lower().strip())
            pattern = rf"(?<!\w){escaped}(?!\w)"
            return len(re.findall(pattern, text))

        # (A) Target Company Match Component (Up to 60 pts)
        title_alias_match = any(has_term(alias, title_lower) for alias in aliases)
        body_alias_match = any(has_term(alias, full_text) for alias in aliases)

        if title_alias_match:
            company_score += 50.0
            # Additional body mentions boost
            body_mentions = sum(count_term(alias, full_text) for alias in aliases)
            if body_mentions > 1:
                company_score += min(10.0, (body_mentions - 1) * 5.0)
            elif body_alias_match:
                company_score += 5.0
        elif body_alias_match:
            company_score += 25.0
            body_mentions = sum(count_term(alias, full_text) for alias in aliases)
            if body_mentions > 1:
                company_score += min(10.0, (body_mentions - 1) * 5.0)

        company_score = min(60.0, company_score)

        # (B) Target Company Keywords Match Component (Up to 40 pts)
        active_keywords = list(keywords) if keywords else list(core_terms)

        kw_title_matches = sum(1 for kw in active_keywords if has_term(kw, title_lower))
        kw_body_matches = sum(1 for kw in active_keywords if has_term(kw, full_text))

        if kw_title_matches > 0:
            keyword_score += min(25.0, kw_title_matches * 15.0)
        if kw_body_matches > 0:
            keyword_score += min(15.0, kw_body_matches * 5.0)

        keyword_score = min(40.0, keyword_score)

        # Total relevance score
        total_score = company_score + keyword_score

        # Guardrail 1: If neither company nor aliases matched anywhere in title or body,
        # an article cannot have high relevance to the target company.
        if not title_alias_match and not body_alias_match:
            total_score = min(20.0, total_score)

        # Guardrail 2: Strict Keyword Requirement
        # If the user explicitly provided keywords, the article MUST match at least one keyword.
        # Otherwise, the article is not relevant to the requested user keywords.
        if keywords and len(keywords) > 0:
            user_kw_matches = sum(1 for kw in keywords if has_term(kw, full_text))
            if user_kw_matches == 0:
                total_score = min(20.0, total_score * 0.3)

        relevance_score = min(100.0, round(total_score, 1))

        # 2. Business Importance Rating & Score (0 - 100)
        importance_score = 40.0 # Baseline MEDIUM importance

        # Check for critical triggers
        critical_count = sum(1 for kw in cls.CRITICAL_IMPORTANCE_KEYWORDS if kw in full_text)
        high_count = sum(1 for kw in cls.HIGH_IMPORTANCE_KEYWORDS if kw in full_text)

        if title_alias_match and critical_count > 0:
            importance_score += 45.0
        elif critical_count > 0:
            importance_score += 35.0

        if high_count > 0:
            importance_score += min(25.0, high_count * 10.0)

        if "record" in title_lower or "billion" in title_lower or "unveils" in title_lower:
            importance_score += 15.0

        importance_score = min(100.0, round(importance_score, 1))

        if importance_score >= 80.0:
            importance_rating = "CRITICAL"
        elif importance_score >= 60.0:
            importance_rating = "HIGH"
        elif importance_score >= 40.0:
            importance_rating = "MEDIUM"
        else:
            importance_rating = "LOW"

        # 3. Sentiment & Impact Tone
        pos_score = sum(1 for kw in cls.POSITIVE_IMPACT_KEYWORDS if kw in full_text)
        risk_score = sum(1 for kw in cls.RISK_THREAT_KEYWORDS if kw in full_text)

        if risk_score > pos_score and risk_score > 0:
            sentiment_tone = "Risk / Threat"
        elif pos_score > risk_score and pos_score > 0:
            if "unveil" in full_text or "launch" in full_text or "platform" in full_text:
                sentiment_tone = "Positive Milestone"
            else:
                sentiment_tone = "Strategic Expansion"
        elif "expansion" in full_text or "partnership" in full_text:
            sentiment_tone = "Strategic Expansion"
        else:
            sentiment_tone = "Neutral"

        # 4. Generate AI Importance Summary & DeepSeek-R1 Reasoning
        deepseek_analysis = deepseek_service_instance.analyze_article(
            title=title_text,
            description=desc_text,
            content=body_text,
            target_entity=company_name,
            keywords=keywords
        )

        ai_summary = cls._generate_ai_summary(
            company_name=company_name,
            title=title_text,
            importance_rating=importance_rating,
            sentiment_tone=sentiment_tone,
            relevance_score=relevance_score
        )

        return {
            "target_entity": company_name,
            "relevance_score": relevance_score,
            "importance_score": importance_score,
            "importance_rating": importance_rating,
            "sentiment_tone": sentiment_tone,
            "ai_summary": ai_summary,
            "reasoning_trace": deepseek_analysis.get("reasoning_trace", "")
        }

    @classmethod
    def _generate_ai_summary(
        cls, company_name: str, title: str, importance_rating: str, sentiment_tone: str, relevance_score: float
    ) -> str:
        """Constructs a comprehensive 3-line AI executive takeaway explaining why the article is important to the target company."""
        clean_title = title.strip() if title else f"Developments concerning {company_name}"
        if not clean_title.endswith('.'):
            clean_title += '.'

        line1 = f"• Event: {clean_title}"
        if relevance_score < 40.0:
            line2 = f"• Strategic Impact: Low relevance match to {company_name} ({relevance_score:.0f}%), mentioning broader industry trends or background mentions."
            line3 = f"• Forward Outlook: Indirect exposure with negligible operational impact on {company_name} core operations."
        else:
            impact_desc = {
                "Positive Milestone": f"Direct positive product or technology advancement strengthening {company_name}'s market position.",
                "Risk / Threat": f"Potential risk, regulatory scrutiny, or competitive headwinds affecting {company_name}.",
                "Strategic Expansion": f"Key operational expansion, partnership, or commercial growth initiative for {company_name}.",
                "Bullish / Opportunity": f"Commercial opportunity and growth momentum for {company_name}'s product ecosystem.",
                "Regulatory Headwind": f"Compliance and regulatory oversight impacting {company_name}'s operational roadmap.",
                "Neutral": f"Business coverage monitoring {company_name}'s ongoing industry activities and market presence."
            }.get(sentiment_tone, f"Strategic industry coverage directly concerning {company_name}.")
            line2 = f"• Strategic Impact: [{importance_rating.upper()} IMPACT] {impact_desc}"
            line3 = f"• Forward Outlook: Target relevance assessed at {relevance_score:.0f}%; recommend tracking subsequent execution milestones."

        return f"{line1}\n{line2}\n{line3}"

    @classmethod
    def filter_by_relevance(
        cls, articles: List[Any], target_entity: str = "All Companies", min_score: float = 60.0
    ) -> List[Any]:
        """Filters articles, keeping only those equal to or above the minimum semantic target relevance score (default >= 60.0)."""
        retained = []
        target = target_entity if (target_entity and target_entity.strip().lower() not in ["all", "all companies"]) else "All Companies"
        for article in articles:
            title = getattr(article, "title", "")
            desc = getattr(article, "description", None)
            content = getattr(article, "content", None)
            analysis = cls.compute_semantic_analysis(title, desc, content, target)

            # Attach scores to article object
            article.target_entity = analysis["target_entity"]
            article.relevance_score = analysis["relevance_score"]
            article.importance_score = analysis["importance_score"]
            article.importance_rating = analysis["importance_rating"]
            article.sentiment_tone = analysis["sentiment_tone"]
            article.ai_summary = analysis["ai_summary"]

            if analysis["relevance_score"] >= min_score:
                retained.append(article)

        return retained
