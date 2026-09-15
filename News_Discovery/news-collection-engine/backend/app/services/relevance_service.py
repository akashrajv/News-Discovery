import re
from typing import Dict, Any, List, Tuple

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
        for key, knowledge in cls.COMPANY_KNOWLEDGE.items():
            if key in entity_clean or entity_clean in key:
                return knowledge

        # Dynamic fallback for custom company names
        words = [w for w in re.findall(r'\w+', entity_clean) if len(w) > 2]
        return {
            "name": entity.strip(),
            "aliases": [entity_clean] + words,
            "core_terms": words
        }

    @classmethod
    def compute_semantic_analysis(
        cls,
        title: str,
        description: str = None,
        content: str = None,
        target_entity: str = "All Companies"
    ) -> Dict[str, Any]:
        """
        Calculates Target Relevance Score (0-100%), Business Importance Rating (CRITICAL, HIGH, MEDIUM, LOW),
        Impact Sentiment, and generates an AI importance summary.
        Supports single entity, comma-separated entities, or 'All Companies'.
        """
        title_text = (title or "").strip()
        desc_text = (description or "").strip()
        body_text = (content or "").strip()
        full_text = f"{title_text} {desc_text} {body_text}".lower()
        title_lower = title_text.lower()

        # Parse target entities (supports single or comma-separated targets)
        if not target_entity or target_entity.strip().lower() in ["all", "all companies"]:
            target_entities_list = ["All Companies"]
        else:
            target_entities_list = [e.strip() for e in target_entity.split(",") if e.strip()]

        if len(target_entities_list) > 1 and "All Companies" not in target_entities_list:
            best_analysis = None
            max_relevance = -1.0
            for single_target in target_entities_list:
                analysis = cls._compute_single_entity_analysis(
                    title_text, desc_text, body_text, full_text, title_lower, single_target
                )
                if analysis["relevance_score"] > max_relevance:
                    max_relevance = analysis["relevance_score"]
                    best_analysis = analysis
            return best_analysis or cls._compute_single_entity_analysis(
                title_text, desc_text, body_text, full_text, title_lower, target_entities_list[0]
            )
        else:
            single_target = target_entities_list[0] if target_entities_list else "All Companies"
            return cls._compute_single_entity_analysis(
                title_text, desc_text, body_text, full_text, title_lower, single_target
            )

    @classmethod
    def _compute_single_entity_analysis(
        cls,
        title_text: str,
        desc_text: str,
        body_text: str,
        full_text: str,
        title_lower: str,
        target_entity: str
    ) -> Dict[str, Any]:
        context = cls.get_company_context(target_entity)
        aliases = context.get("aliases", [])
        core_terms = context.get("core_terms", [])
        company_name = context.get("name", target_entity or "Target Company")

        # 1. Target Relevance Score Calculation (0 - 100%)
        relevance_score = 0.0
        title_alias_match = False

        if not target_entity or target_entity.lower() in ["all", "all companies"]:
            # If monitoring all companies, evaluate general company mentions
            any_known = any(comp in full_text for comp_key in cls.COMPANY_KNOWLEDGE for comp in cls.COMPANY_KNOWLEDGE[comp_key]["aliases"])
            relevance_score = 85.0 if any_known else 60.0
            title_alias_match = any_known
        else:
            # Check title matches (Heavy Weight: up to +60 points)
            title_alias_match = any(alias in title_lower for alias in aliases)
            if title_alias_match:
                relevance_score += 60.0
            elif any(term in title_lower for term in core_terms):
                relevance_score += 35.0

            # Check description/body matches (up to +30 points)
            body_alias_match_count = sum(1 for alias in aliases if alias in full_text)
            if body_alias_match_count > 0:
                relevance_score += min(30.0, body_alias_match_count * 15.0)

            # Core terms co-occurrence (+10 points)
            core_matches = sum(1 for term in core_terms if term in full_text)
            if core_matches > 0:
                relevance_score += min(10.0, core_matches * 5.0)

            # Cap at 100%
            relevance_score = min(100.0, round(relevance_score, 1))

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

        # 4. Generate AI Importance Summary
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
            "ai_summary": ai_summary
        }

    @classmethod
    def _generate_ai_summary(
        cls, company_name: str, title: str, importance_rating: str, sentiment_tone: str, relevance_score: float
    ) -> str:
        """Constructs concise AI executive takeaway explaining why the article is important to the target company."""
        if relevance_score < 40.0:
            return f"Low relevance match to {company_name}. Mentions broader industry trends or generic market context."

        impact_desc = {
            "Positive Milestone": f"Direct positive product or technology advancement impacting {company_name}'s market position.",
            "Risk / Threat": f"Potential risk, regulatory scrutiny, or competitive threat affecting {company_name}.",
            "Strategic Expansion": f"Key operational expansion, partnership, or market growth initiative for {company_name}.",
            "Neutral": f"Relevant business coverage monitoring {company_name}'s industry activities and developments."
        }.get(sentiment_tone, f"Strategic coverage concerning {company_name}.")

        return f"[{importance_rating} IMPACT] {impact_desc} (Relevance: {relevance_score:.0f}%)"

    @classmethod
    def filter_by_relevance(
        cls, articles: List[Any], target_entity: str = "All Companies", min_score: float = 30.0
    ) -> List[Any]:
        """Filters articles, keeping only those above the minimum semantic target relevance score."""
        if not target_entity or target_entity.strip().lower() in ["all", "all companies"]:
            return articles

        retained = []
        for article in articles:
            title = getattr(article, "title", "")
            desc = getattr(article, "description", None)
            content = getattr(article, "content", None)
            analysis = cls.compute_semantic_analysis(title, desc, content, target_entity)

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
