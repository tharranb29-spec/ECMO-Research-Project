#!/usr/bin/env python3

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request

from ecmo_seed_ranker import load_seed_records, rank_records, write_json, write_markdown


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
SEED_PATH = ROOT / "data" / "seed_ligands.json"
EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

SEARCH_QUERIES = [
    {
        "target_receptor": "Siglec-9",
        "query": '(Siglec-9 OR SIGLEC9) AND (ligand OR glycomimetic OR agonist OR peptide OR sialoside) sort_date:y',
    },
    {
        "target_receptor": "SIRPa",
        "query": '("SIRPalpha" OR "SIRPa" OR "SIRPα" OR CD47) AND (ligand OR mimetic OR peptide OR variant OR agonist) sort_date:y',
    },
]

NAME_PATTERNS = [
    re.compile(r"\b(pS9L(?:-sol)?|pLac|sLeX|MTTSNeu5Ac|BTCNeu5Ac|N3612|CV1|TTI-621|TTI-622|AO-176|Self peptide|CD47 ectodomain)\b", re.I),
    re.compile(r"\b([A-Z][A-Za-z0-9-]{2,24})\s+(?:peptide|ligand|glycomimetic|agonist|mimetic|variant)\b"),
    re.compile(r"\b(?:peptide|ligand|glycomimetic|agonist|mimetic|variant)\s+([A-Z][A-Za-z0-9-]{2,24})\b"),
]

MODALITY_RULES = [
    ("glycomimetic", "glycomimetic"),
    ("glycopolypeptide", "glycopolypeptide"),
    ("peptide", "peptide"),
    ("protein", "protein"),
    ("variant", "engineered_protein"),
    ("antibody", "antibody"),
    ("fusion", "fusion_protein"),
]


def ensure_outputs():
    OUTPUTS.mkdir(parents=True, exist_ok=True)


def fetch_europe_pmc_results(query, page_size=15):
    params = parse.urlencode(
        {
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": str(page_size),
        }
    )
    url = f"{EUROPE_PMC_SEARCH}?{params}"
    with request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip())


def guess_modality(text):
    lowered = text.lower()
    for needle, modality in MODALITY_RULES:
        if needle in lowered:
            return modality
    return "literature_lead"


def extract_candidate_names(text):
    candidates = []
    for pattern in NAME_PATTERNS:
        for match in pattern.findall(text):
            name = match if isinstance(match, str) else match[0]
            name = normalize_name(name)
            if len(name) < 3:
                continue
            if name.lower() in {"siglec", "ligand", "peptide", "agonist", "variant", "cd47", "sirpa"}:
                continue
            candidates.append(name)
    deduped = []
    seen = set()
    for name in candidates:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(name)
    return deduped[:6]


def article_link(article):
    source = article.get("source")
    article_id = article.get("id")
    if source and article_id:
        return f"https://europepmc.org/article/{source}/{article_id}"
    return ""


def score_lead(article, candidate_name, target_receptor):
    text = f"{article.get('title', '')} {article.get('abstractText', article.get('abstract', ''))}".lower()
    score = 45
    if candidate_name.lower() in text:
        score += 10
    if "high-affinity" in text or "high affinity" in text:
        score += 8
    if "agonist" in text or "mimetic" in text or "glycomimetic" in text:
        score += 7
    if "inhibit" in text or "immune" in text or "inflammatory" in text:
        score += 5
    if target_receptor.lower().replace("-", "") in text.replace("-", ""):
        score += 10
    return min(score, 92)


def build_article_record(article, target_receptor, query):
    return {
        "id": f"{article.get('source', 'SRC')}-{article.get('id', '')}",
        "target_receptor": target_receptor,
        "query": query,
        "title": article.get("title", ""),
        "abstract": article.get("abstractText", ""),
        "author_string": article.get("authorString", ""),
        "journal_title": article.get("journalTitle", ""),
        "publication_date": article.get("firstPublicationDate") or article.get("pubYear"),
        "doi": article.get("doi", ""),
        "source_url": article_link(article),
    }


def build_leads_from_article(article_record):
    text = f"{article_record['title']} {article_record['abstract']}"
    names = extract_candidate_names(text)
    leads = []
    for name in names:
        modality = guess_modality(text)
        score = score_lead(article_record, name, article_record["target_receptor"])
        leads.append(
            {
                "candidate_name": name,
                "target_receptor": article_record["target_receptor"],
                "modality_guess": modality,
                "lead_score": score,
                "lead_type": "literature_candidate_lead",
                "rationale": f"Recent literature mention in article: {article_record['title']}",
                "publication_date": article_record["publication_date"],
                "source_title": article_record["title"],
                "source_url": article_record["source_url"],
            }
        )
    return leads


def classify_known_seed(lead_name, seed_records):
    normalized = lead_name.lower()
    for record in seed_records:
        if record["candidate_name"].lower() == normalized:
            return True
    return False


def score_feature(base, bump=0.0, low=0.02, high=0.98):
    return max(low, min(high, round(base + bump, 3)))


def build_candidate_from_lead(lead, seed_records):
    text = f"{lead.get('source_title', '')} {lead.get('rationale', '')}".lower()
    normalized_name = lead["candidate_name"].strip().lower().replace(" ", "_")
    lead_strength = lead["lead_score"] / 100.0

    affinity = score_feature(0.34 + lead_strength * 0.40, 0.08 if "high-affinity" in text or "high affinity" in text else 0.0)
    specificity = score_feature(0.40 + lead_strength * 0.34, 0.10 if lead["target_receptor"].lower().replace("-", "") in text.replace("-", "") else 0.0)
    functional = score_feature(0.20 + lead_strength * 0.38, 0.10 if any(word in text for word in ["immune", "inhibit", "inflammatory", "netosis", "macrophage"]) else 0.0)
    surface = score_feature(0.18 + lead_strength * 0.20, 0.10 if any(word in text for word in ["surface", "material", "coating", "biomaterial", "interface"]) else 0.0)
    conjugation = score_feature(0.38 + (0.18 if lead["modality_guess"] in {"peptide", "glycomimetic"} else 0.04))
    hemocompatibility = score_feature(0.36 + lead_strength * 0.22, 0.10 if any(word in text for word in ["blood", "platelet", "hemocompat", "thrombo", "hemolysis"]) else 0.0)
    clustering = score_feature(0.22 + lead_strength * 0.16, 0.18 if "multivalent" in text or "cluster" in text or "poly" in text else 0.0)
    literature_confidence = score_feature(0.45 + lead_strength * 0.42)

    discovery_status = "known_reference" if classify_known_seed(lead["candidate_name"], seed_records) else "new_literature_lead"

    return {
        "id": f"auto_{normalized_name}_{lead['target_receptor'].lower().replace('-', '')}",
        "candidate_name": lead["candidate_name"],
        "target_receptor": lead["target_receptor"],
        "modality": lead["modality_guess"],
        "affinity_uM": None,
        "affinity_note": "Provisional feature estimate derived from recent literature lead, not a measured KD.",
        "affinity_strength_score": affinity,
        "specificity_score": specificity,
        "functional_immunomodulation_score": functional,
        "surface_validation_score": surface,
        "conjugation_feasibility_score": conjugation,
        "hemocompatibility_proxy_score": hemocompatibility,
        "multivalency_or_clustering_score": clustering,
        "literature_confidence_score": literature_confidence,
        "training_label_score": None,
        "training_label": None,
        "evidence_summary": f"{lead['rationale']} ({discovery_status.replace('_', ' ')})",
        "source_urls": [lead["source_url"]] if lead.get("source_url") else [],
        "discovery_status": discovery_status,
        "lead_score": lead["lead_score"],
        "publication_date": lead.get("publication_date"),
        "source_title": lead.get("source_title"),
    }


def dedupe_leads(leads):
    ordered = sorted(leads, key=lambda item: (-item["lead_score"], item["candidate_name"].lower()))
    deduped = []
    seen = set()
    for lead in ordered:
        key = (lead["candidate_name"].lower(), lead["target_receptor"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(lead)
    return deduped


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def refresh_research_outputs():
    ensure_outputs()
    seed_records = load_seed_records(SEED_PATH)
    fetched_articles = []
    discovered_leads = []

    for entry in SEARCH_QUERIES:
        payload = fetch_europe_pmc_results(entry["query"])
        for result in payload.get("resultList", {}).get("result", []):
            article_record = build_article_record(result, entry["target_receptor"], entry["query"])
            fetched_articles.append(article_record)
            discovered_leads.extend(build_leads_from_article(article_record))

    deduped_leads = dedupe_leads(discovered_leads)
    autonomous_candidates = [build_candidate_from_lead(lead, seed_records) for lead in deduped_leads]
    autonomous_ranking = rank_records(seed_records, autonomous_candidates) if autonomous_candidates else {"models": {}, "metrics": {}, "ranked": []}
    candidate_index = {candidate["id"]: candidate for candidate in autonomous_candidates}
    for row in autonomous_ranking.get("ranked", []):
        candidate = candidate_index.get(row["id"], {})
        row["lead_score"] = candidate.get("lead_score")
        row["discovery_status"] = candidate.get("discovery_status")
        row["publication_date"] = candidate.get("publication_date")
        row["source_title"] = candidate.get("source_title")

    summary = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "article_count": len(fetched_articles),
        "lead_count": len(deduped_leads),
        "autonomous_ranked_count": len(autonomous_ranking.get("ranked", [])),
        "queries": SEARCH_QUERIES,
    }

    write_json(OUTPUTS / "research_articles.json", {"last_updated": summary["last_updated"], "articles": fetched_articles})
    write_json(OUTPUTS / "research_leads.json", {"last_updated": summary["last_updated"], "leads": deduped_leads})
    write_json(OUTPUTS / "autonomous_candidates.json", {"last_updated": summary["last_updated"], "candidates": autonomous_candidates})
    write_json(OUTPUTS / "autonomous_ranking_results.json", autonomous_ranking)
    write_markdown(OUTPUTS / "autonomous_ranking_report.md", autonomous_ranking, "outputs/autonomous_candidates.json")
    write_json(OUTPUTS / "research_status.json", summary)
    return summary


if __name__ == "__main__":
    summary = refresh_research_outputs()
    print(json.dumps(summary, indent=2))
