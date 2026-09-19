import json
import re
from typing import Dict, Any, List, Optional
import httpx

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("news_engine.deepseek_service")


class DeepSeekService:
    """
    DeepSeek-R1 AI Reasoning Engine for deep semantic news analysis.
    Uses DeepSeek-R1 (deepseek-reasoner) to evaluate target relevance,
    business importance impact, sentiment tone, executive takeaways,
    and captures the explicit cognitive <think> reasoning chain.
    """

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = (settings.DEEPSEEK_BASE_URL or "https://api.deepseek.com").rstrip("/")
        self.model = settings.DEEPSEEK_MODEL or "deepseek-reasoner"
        self.http_timeout = 15.0

    @property
    def is_configured(self) -> bool:
        """Returns True if a live DeepSeek API key is configured."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def analyze_article(
        self,
        title: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        target_entity: str = "All Companies",
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Executes DeepSeek-R1 reasoning analysis on an article.
        Returns relevance_score, importance_score, importance_rating,
        sentiment_tone, ai_summary, and reasoning_trace.
        """
        title_clean = (title or "").strip()
        desc_clean = (description or "").strip()
        body_clean = (content or "").strip()[:1500]  # First 1500 chars excerpt
        keywords_str = ", ".join(keywords) if keywords else "None specified"

        # If live API key is available, call DeepSeek-R1 (deepseek-reasoner)
        if self.is_configured:
            try:
                result = self._call_deepseek_api(
                    title=title_clean,
                    description=desc_clean,
                    content=body_clean,
                    target_entity=target_entity,
                    keywords_str=keywords_str
                )
                if result:
                    return result
            except Exception as e:
                logger.warning(f"DeepSeek-R1 API call failed ({e}). Falling back to local reasoning simulation.")

        # Fallback to local intelligent reasoning analyzer
        return self._local_reasoning_analysis(
            title=title_clean,
            description=desc_clean,
            content=body_clean,
            target_entity=target_entity,
            keywords=keywords or []
        )

    def _call_deepseek_api(
        self,
        title: str,
        description: str,
        content: str,
        target_entity: str,
        keywords_str: str
    ) -> Optional[Dict[str, Any]]:
        """Invokes DeepSeek-R1 endpoint and captures reasoning_content."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        system_prompt = (
            "You are DeepSeek-R1, an elite financial and enterprise intelligence analyst. "
            "Analyze the news article against the requested target entity. "
            "Think step-by-step to evaluate relevance and strategic importance. "
            "Output your final decision strictly as a valid JSON object with the following keys:\n"
            "{\n"
            '  "target_entity": "Identified company or requested target",\n'
            '  "relevance_score": float between 0.0 and 100.0,\n'
            '  "importance_score": float between 0.0 and 100.0,\n'
            '  "importance_rating": "CRITICAL" | "HIGH" | "MEDIUM" | "LOW",\n'
            '  "sentiment_tone": "Bullish / Opportunity" | "Risk / Threat" | "Regulatory Headwind" | "Neutral",\n'
            '  "ai_summary": "Comprehensive 3-line executive summary strictly structured across three lines (Line 1: Core event & development; Line 2: Strategic impact & organizational relevance; Line 3: Forward outlook and key operational takeaway)"\n'
            "}"
        )

        user_content = (
            f"Target Entity: {target_entity}\n"
            f"Keywords: {keywords_str}\n\n"
            f"Article Headline: {title}\n"
            f"Description: {description}\n"
            f"Content Excerpt: {content}\n\n"
            "Please analyze relevance, impact, and provide your JSON assessment."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }

        with httpx.Client(timeout=self.http_timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})

                # In DeepSeek-R1 (deepseek-reasoner), reasoning thoughts are returned in reasoning_content
                reasoning_trace = message.get("reasoning_content") or ""
                content_text = message.get("content", "")

                # Parse JSON block from response content
                parsed_json = self._extract_json(content_text)
                if parsed_json:
                    return {
                        "target_entity": parsed_json.get("target_entity", target_entity),
                        "relevance_score": float(parsed_json.get("relevance_score", 70.0)),
                        "importance_score": float(parsed_json.get("importance_score", 50.0)),
                        "importance_rating": str(parsed_json.get("importance_rating", "MEDIUM")).upper(),
                        "sentiment_tone": str(parsed_json.get("sentiment_tone", "Neutral")),
                        "ai_summary": str(parsed_json.get("ai_summary", title)),
                        "reasoning_trace": reasoning_trace or f"DeepSeek-R1 evaluation completed for {target_entity}."
                    }
            else:
                logger.warning(f"DeepSeek API responded with HTTP {response.status_code}: {response.text}")
        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON object from model output text."""
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # Try regex search for markdown fenced JSON or brace block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return None

    def _local_reasoning_analysis(
        self,
        title: str,
        description: str,
        content: str,
        target_entity: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """
        Deterministic local reasoning engine that mirrors DeepSeek-R1's structured
        <think> cognitive chain-of-thought and strategic scoring.
        """
        full_text = f"{title} {description} {content}".lower()
        title_lower = title.lower()

        # Build DeepSeek-R1 style reasoning thoughts
        thoughts = []
        thoughts.append(f"1. Target Entity Identification: Evaluating target query '{target_entity}'.")

        # Entity match verification
        clean_target = target_entity.strip().lower()
        aliases = [clean_target] if clean_target not in ["all", "all companies"] else ["nvidia", "tesla", "apple", "microsoft", "tata motors", "openai"]

        # Add domain aliases
        alias_map = {
            "nvidia": ["nvidia", "nvda", "blackwell", "hopper", "cuda", "jensen huang"],
            "tesla": ["tesla", "tsla", "elon musk", "robotaxi", "cybercab", "fsd"],
            "apple": ["apple", "aapl", "iphone", "macbook", "apple intelligence", "tim cook"],
            "microsoft": ["microsoft", "msft", "copilot", "azure", "satya nadella"],
            "tata motors": ["tata motors", "tata motor", "tata nexon", "jlr", "jaguar land rover"],
            "openai": ["openai", "open ai", "chatgpt", "sam altman", "gpt-4", "gpt-5", "sora"],
            "open ai": ["openai", "open ai", "chatgpt", "sam altman", "gpt-4", "gpt-5", "sora"]
        }
        for k, v in alias_map.items():
            if k in clean_target or clean_target in k:
                aliases.extend(v)
        aliases = list(dict.fromkeys(aliases))

        def has_term(term: str, text: str) -> bool:
            if not term or not text:
                return False
            escaped = re.escape(term.strip())
            pattern = rf"(?<!\w){escaped}(?!\w)"
            return bool(re.search(pattern, text))

        title_match = any(has_term(a, title_lower) for a in aliases)
        body_match = any(has_term(a, full_text) for a in aliases)

        # Relevance scoring with DeepSeek-R1 reasoning
        relevance_score = 0.0
        if title_match:
            relevance_score += 55.0
            thoughts.append(f"2. Headline Signal: Primary target entity '{target_entity}' is explicitly named in the headline. High prominence established (+55%).")
        elif body_match:
            relevance_score += 25.0
            thoughts.append(f"2. Body Mention: Target entity '{target_entity}' appears in the article body or summary (+25%).")
        else:
            thoughts.append(f"2. No Direct Entity Match: Headline and excerpt do not mention '{target_entity}'. Applying strict relevance guardrail.")

        # Keywords relevance
        kw_matches = sum(1 for kw in keywords if has_term(kw.lower(), full_text)) if keywords else 0
        if kw_matches > 0:
            boost = min(25.0, kw_matches * 10.0)
            relevance_score += boost
            thoughts.append(f"3. Keyword Co-occurrence: Found {kw_matches} user keyword matches in text (+{boost:.0f}%).")
        else:
            if keywords and len(keywords) > 0:
                relevance_score = min(20.0, relevance_score * 0.3)
                thoughts.append("3. Keyword Guardrail: User specified target keywords, but 0 matches found in text. Limiting relevance score below threshold.")
            else:
                thoughts.append("3. Keyword Check: No user keywords specified.")

        if not title_match and not body_match:
            relevance_score = min(20.0, relevance_score)

        relevance_score = min(100.0, round(relevance_score, 1))
        thoughts.append(f"4. Relevance Conclusion: Final target relevance scored at {relevance_score:.0f}%.")

        # Business Importance & Impact Rating
        importance_score = 45.0
        importance_rating = "MEDIUM"
        critical_triggers = ["acquisition", "merger", "antitrust", "lawsuit", "investigation", "bankruptcy", "sanctions", "ceo steps down", "layoffs"]
        high_triggers = ["unveils", "announces", "launches", "expansion", "partnership", "record sales", "forecast", "breakthrough", "earnings", "revenue"]

        if any(w in full_text for w in critical_triggers):
            importance_rating = "CRITICAL"
            importance_score = 90.0
            thoughts.append("5. Strategic Impact: Critical regulatory, legal, or M&A indicators detected. Rated CRITICAL.")
        elif any(w in full_text for w in high_triggers):
            importance_rating = "HIGH"
            importance_score = 75.0
            thoughts.append("5. Strategic Impact: Product launch, breakthrough, or earnings expansion detected. Rated HIGH.")
        else:
            thoughts.append("5. Strategic Impact: Routine operational or general coverage. Rated MEDIUM.")

        # Sentiment Tone
        sentiment_tone = "Neutral"
        if any(w in full_text for w in ["record", "surge", "growth", "breakthrough", "expansion", "profit", "win"]):
            sentiment_tone = "Bullish / Opportunity"
        elif any(w in full_text for w in ["lawsuit", "investigation", "decline", "fall", "penalty", "breach", "threat"]):
            sentiment_tone = "Risk / Threat"
        elif any(w in full_text for w in ["regulatory", "sec", "antitrust", "ban", "compliance"]):
            sentiment_tone = "Regulatory Headwind"

        thoughts.append(f"6. Sentiment Synthesis: Classified as '{sentiment_tone}'.")

        # Synthesize 3-Line AI Executive Summary
        headline_clean = title.strip() if title else f"Developments involving {target_entity}"
        if not headline_clean.endswith('.'):
            headline_clean += '.'

        if relevance_score >= 60.0:
            line1 = f"• Event: {headline_clean}"
            line2 = f"• Strategic Impact: [{importance_rating.upper()} IMPACT] Identified direct organizational development for {target_entity} with strong market alignment ({relevance_score:.0f}% relevance)."
            line3 = f"• Forward Outlook: {sentiment_tone} trajectory; tracking operational rollouts, competitive response, and enterprise revenue implications."
            summary = f"{line1}\n{line2}\n{line3}"
        elif relevance_score >= 30.0:
            line1 = f"• Event: {headline_clean}"
            line2 = f"• Sector Context: [{importance_rating.upper()} IMPACT] Peripheral industry developments relating indirectly to the {target_entity} ecosystem ({relevance_score:.0f}% relevance)."
            line3 = f"• Forward Outlook: Evaluated as secondary monitoring priority with moderate near-term commercial implications."
            summary = f"{line1}\n{line2}\n{line3}"
        else:
            line1 = f"• Event: {headline_clean}"
            line2 = f"• Context: Peripheral coverage with negligible direct operational link to {target_entity} ({relevance_score:.0f}% relevance)."
            line3 = f"• Forward Outlook: Classified as background industry noise for {target_entity} strategic tracking."
            summary = f"{line1}\n{line2}\n{line3}"

        reasoning_trace = "\n".join(thoughts)

        return {
            "target_entity": target_entity,
            "relevance_score": relevance_score,
            "importance_score": importance_score,
            "importance_rating": importance_rating,
            "sentiment_tone": sentiment_tone,
            "ai_summary": summary,
            "reasoning_trace": reasoning_trace
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns DeepSeek-R1 operational status."""
        return {
            "status": "ready" if self.is_configured else "local_reasoner_active",
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": self.is_configured
        }


# Global singleton instance
deepseek_service_instance = DeepSeekService()
