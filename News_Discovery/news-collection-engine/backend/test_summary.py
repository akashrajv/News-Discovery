import re
from app.services.relevance_service import RelevanceService

def test_gen(company_name, title, importance_rating, sentiment_tone, relevance_score, description="", content="", keywords=None):
    full_text = f"{title or ''} {description or ''} {content or ''}".strip()
    full_text_lower = full_text.lower()
    title_lower = (title or "").lower()

    target_display = company_name or "Target Company"
    if target_display.lower() in ["all", "all companies", "target company"]:
        for key, kdata in RelevanceService.COMPANY_KNOWLEDGE.items():
            if any(alias in full_text_lower for alias in kdata["aliases"]):
                target_display = kdata["name"]
                break

    if relevance_score < 40.0:
        return (
            f"[{importance_rating} IMPACT] Low relevance match to {target_display} (Relevance: {relevance_score:.0f}%).\n\n"
            f"• Executive Overview: The article centers on broader market developments or tangential industry coverage without substantive strategic focus on {target_display}.\n"
            f"• Strategic Impact: Negligible direct commercial or operational exposure for {target_display}.\n"
            f"• Watchpoint: Routine monitoring only; no portfolio or operational adjustments warranted."
        )

    desc_clean = re.sub(r'<[^>]+>', ' ', description or '')
    desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()
    desc_clean = re.sub(r'(?i)(the post .* appeared first on .*|read more .*|continue reading .*)', '', desc_clean).strip()

    extra_context = ""
    if desc_clean:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', desc_clean) if len(s.strip()) > 20]
        filtered_sentences = [s for s in sentences[:2] if s.lower() not in title_lower]
        if filtered_sentences:
            extra_context = " ".join(filtered_sentences)

    if any(k in full_text_lower for k in ["acquisition", "merger", "buyout", "acquire"]):
        dev_theme = "Strategic M&A & Infrastructure Consolidation"
        action_desc = f"{target_display} is involved in major merger and acquisition activity or strategic consolidation."
        impact_detail = f"Significantly alters competitive landscape and asset concentration, creating immediate portfolio synergies and expanded market footprint for {target_display}."
        signals = "Monitor antitrust regulatory clearances, integration timelines, balance sheet leverage, and accretion to earnings."
    elif any(k in full_text_lower for k in ["earnings", "revenue", "profit", "quarterly", "fiscal", "guidance"]):
        dev_theme = "Financial Performance & Operating Guidance"
        action_desc = f"{target_display}'s financial disclosures, quarterly earnings, or operational performance metrics were reported."
        impact_detail = f"Directly influences investor sentiment, valuation multiples, and institutional capital flows for {target_display}."
        signals = "Watch gross margin trends, operational cash flows, forward guidance revisions, and sell-side consensus adjustments."
    elif any(k in full_text_lower for k in ["lawsuit", "sec ", "investigation", "antitrust", "recall", "penalty", "sanctions"]):
        dev_theme = "Regulatory Scrutiny & Legal Risk Exposure"
        action_desc = f"{target_display} is facing regulatory scrutiny, legal litigation, or compliance inquiries."
        impact_detail = f"Presents operational risk, potential fines, or brand equity exposure that could impact {target_display}'s operational flexibility."
        signals = "Track legal defense developments, regulatory settlements, risk reserves, and compliance remediation milestones."
    elif any(k in full_text_lower for k in ["unveils", "announces", "launches", "architecture", "breakthrough", "next-generation", "platform"]):
        dev_theme = "Product Innovation & Technology Breakthrough"
        action_desc = f"{target_display} has announced new technology, architecture, or product lineup expansion."
        impact_detail = f"Strengthens {target_display}'s technological moat and product differentiation, fortifying commercial competitive advantage against rivals."
        signals = "Monitor product delivery timelines, customer adoption rate, ecosystem partner integration, and production ramp-up."
    elif any(k in full_text_lower for k in ["expansion", "partnership", "joint venture", "factory", "gigafactory", "investment"]):
        dev_theme = "Commercial Scaling & Strategic Expansion"
        action_desc = f"{target_display} is advancing strategic partnerships, infrastructure capacity, or market expansion initiatives."
        impact_detail = f"Accelerates operational scale, enhances supply chain resilience, and expands addressable target markets for {target_display}."
        signals = "Examine capital expenditure commitments, capacity utilization milestones, and revenue contribution from new partners."
    else:
        dev_theme = "Strategic Industry Coverage & Market Dynamics"
        action_desc = f"Industry coverage detailing operational developments and market dynamics concerning {target_display}."
        impact_detail = f"Provides ongoing market intelligence regarding {target_display}'s competitive position and sectoral trend alignment."
        signals = "Track broader sector velocity, peer movements, and shifting customer demand signals."

    quant_matches = re.findall(r'(\$\d+(?:\.\d+)?\s*(?:billion|million|B|M)?|\d+(?:\.\d+)?%|\d+\s*(?:horsepower|km|miles|kwh|nm))', full_text, re.IGNORECASE)
    quant_str = ""
    if quant_matches:
        unique_quants = list(dict.fromkeys(quant_matches))[:3]
        quant_str = f" Key metrics highlighted: {', '.join(unique_quants)}."

    title_summary = title.strip()
    if not title_summary.endswith('.'):
        title_summary += '.'

    if extra_context:
        overview_text = f"{title_summary} {extra_context}"
    else:
        overview_text = f"{title_summary} {action_desc}"

    return (
        f"[{importance_rating} IMPACT] {dev_theme} (Relevance: {relevance_score:.0f}%)\n\n"
        f"• Executive Overview: {overview_text}{quant_str}\n"
        f"• Strategic Impact: {impact_detail}\n"
        f"• Market Signals & Watchpoints: {signals}"
    )

print('--- CASE 1: NVIDIA M&A ---')
print(test_gen('NVIDIA', 'NVIDIA Announces Acquisition of Next-Gen AI Chip Maker for $10 Billion', 'CRITICAL', 'Positive Milestone', 95.0, 'NVIDIA unveils massive expansion into data center GPUs and supercomputers.'))

print('\n--- CASE 2: Tata Motors All Companies ---')
print(test_gen('All Companies', 'Tata Motors announces new electric vehicle platform', 'HIGH', 'Positive Milestone', 85.0, 'Tata Motors unveils its next-generation EV architecture aimed at expanding range and lowering manufacturing costs across its SUV lineup.'))

print('\n--- CASE 3: Low relevance ---')
print(test_gen('Apple', 'Local Bakery Wins Annual Baking Contest', 'LOW', 'Neutral', 20.0, 'A local bakery won first prize for best apple pie in county fair.'))
