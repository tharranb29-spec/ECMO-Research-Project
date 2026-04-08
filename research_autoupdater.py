#!/usr/bin/env python3

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request

from ecmo_seed_ranker import load_seed_records, normalize_target_receptor, rank_records, write_markdown


ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / "outputs"
SEED_PATH = ROOT / "data" / "seed_ligands.json"
EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
AUTO_RESEARCH_MAX_ARTICLES = int(os.environ.get("AUTO_RESEARCH_MAX_ARTICLES", "12"))
AUTO_RESEARCH_PAGE_SIZE = int(os.environ.get("AUTO_RESEARCH_PAGE_SIZE", "24"))
AUTO_RESEARCH_LLM_ENABLED = os.environ.get("AUTO_RESEARCH_LLM_ENABLED", "1").strip().lower() not in {"0", "false", "no"}

SEARCH_QUERIES = [
    {
        "target_receptor": "Siglec-9",
        "query": '((Siglec-9 OR SIGLEC9) AND (ligand OR glycomimetic OR glycan OR glycopolypeptide OR glycopeptide OR agonist OR peptide OR sialoside OR sialic OR engineered OR synthetic OR high-affinity)) sort_date:y',
    },
    {
        "target_receptor": "Siglec-9",
        "query": '((Siglec-9 OR SIGLEC9) AND (pS9L OR pLac OR sLeX OR glycomimetic OR glycopolypeptide OR multivalent OR sialoside)) sort_date:y',
    },
    {
        "target_receptor": "SIRPa",
        "query": '((\"SIRPalpha\" OR \"SIRPa\" OR \"SIRPα\" OR CD47) AND (ligand OR mimetic OR peptide OR variant OR agonist OR bispecific OR antibody OR ectodomain OR decoy OR fusion OR high-affinity OR engineered)) sort_date:y',
    },
    {
        "target_receptor": "SIRPa",
        "query": '((\"SIRPalpha\" OR \"SIRPa\" OR \"SIRPα\" OR CD47) AND (\"self peptide\" OR ectodomain OR N3612 OR CV1 OR TTI-621 OR TTI-622 OR bispecific OR antibody OR decoy)) sort_date:y',
    },
]

HISTORY_PATH = OUTPUTS / "research_history.json"

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

IGNORED_CANDIDATE_TERMS = {
    "siglec",
    "siglec 9",
    "siglec9",
    "sirpa",
    "sirpalpha",
    "cd47",
    "sting",
    "cgamp",
    "nets",
    "ros",
    "tnf",
    "tnf alpha",
    "il 10",
    "macrophage",
    "neutrophil",
    "tumor",
    "immune",
    "immunity",
    "inflammation",
    "checkpoint",
    "ligand",
    "agonist",
    "peptide",
    "protein",
    "variant",
    "mimetic",
    "glycomimetic",
    "sialoside",
    "receptor",
    "construct",
    "conjugate",
    "antibody",
    "fusion protein",
}

ALLOW_SIGNAL_WORDS = {
    "peptide",
    "glycomimetic",
    "glycopeptide",
    "glycopolypeptide",
    "sialoside",
    "mimetic",
    "antibody",
    "protein",
    "variant",
    "fusion",
    "ligand",
    "ectodomain",
    "scaffold",
    "decoy",
    "construct",
    "polypeptide",
    "glycan",
    "copy",
    "soluble",
}

EXACT_BLOCKED_CANDIDATE_TERMS = {
    "siglec",
    "siglec 9",
    "siglec9",
    "sirpa",
    "sirpalpha",
    "cd47",
    "sting",
    "cgamp",
    "ros",
    "tnf",
    "tnf alpha",
    "il 10",
    "macrophage",
    "neutrophil",
    "immune",
    "immunity",
    "inflammation",
    "checkpoint",
    "ligand",
    "agonist",
    "peptide",
    "protein",
    "variant",
    "mimetic",
    "glycomimetic",
    "sialoside",
    "receptor",
    "construct",
    "conjugate",
    "antibody",
    "fusion protein",
}

TARGET_DISCOVERY_TERMS = {
    "Siglec-9": {
        "positive": {
            "glycomimetic",
            "glycan",
            "glycopolypeptide",
            "glycopeptide",
            "sialic",
            "sialoside",
            "slex",
            "ps9l",
            "plac",
            "engineered",
            "synthetic",
            "high-affinity",
            "agonist",
            "ligand",
            "mimetic",
        },
        "negative": {
            "urticaria",
            "allergic",
            "crohn",
            "sepsis",
            "adjuvant",
            "rhinitis",
        },
    },
    "SIRPa": {
        "positive": {
            "cd47",
            "self peptide",
            "self",
            "ectodomain",
            "variant",
            "bispecific",
            "decoy",
            "fusion",
            "antibody",
            "mimetic",
            "engineered",
            "high-affinity",
            "checkpoint",
        },
        "negative": {
            "tumor microenvironment",
            "radiotherapy",
            "microglia",
            "glioma",
            "macrophage polarization",
        },
    },
}


def ensure_outputs():
    OUTPUTS.mkdir(parents=True, exist_ok=True)


def fetch_europe_pmc_results(query, page_size=AUTO_RESEARCH_PAGE_SIZE):
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


def canonical_key(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def sanitize_candidate_name(name):
    cleaned = normalize_name(
        str(name or "")
        .replace("–", "-")
        .replace("—", "-")
        .replace("α", "alpha")
        .replace('"', "")
        .replace("'", "")
        .replace("(", " ")
        .replace(")", " ")
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:-")
    return cleaned


def candidate_is_allowed(name, seed_records=None):
    cleaned = sanitize_candidate_name(name)
    key = canonical_key(cleaned)
    if seed_records:
        for record in seed_records:
            if canonical_key(record.get("candidate_name", "")) == key:
                return True
    if len(cleaned) < 3:
        return False
    if key in EXACT_BLOCKED_CANDIDATE_TERMS:
        return False
    if any(fragment in key for fragment in ["sting", "cgamp", "macrophage", "neutrophil", "inflammation", "immune", "checkpoint", "receptor"]):
        return False
    if (key.startswith("anti ") or key.startswith("anti-")) and any(token in key for token in ["sirpa", "sirpalpha", "siglec", "cd47"]):
        return False
    generic_tokens = set(key.split())
    receptor_tokens = {"siglec", "siglec9", "sirpa", "sirpalpha", "cd47"}
    modality_tokens = {"antibody", "protein", "peptide", "mimetic", "glycomimetic", "ligand", "agonist", "construct", "fusion"}
    if generic_tokens & receptor_tokens and generic_tokens & modality_tokens and not re.search(r"\d", cleaned):
        return False
    has_signal_word = any(word in key for word in ALLOW_SIGNAL_WORDS)
    looks_like_alias = bool(re.search(r"\d", cleaned)) or bool(re.search(r"[A-Z].*[a-z]|[a-z].*[A-Z]", cleaned))
    if has_signal_word or looks_like_alias:
        return True
    return False


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
            name = sanitize_candidate_name(name)
            if not candidate_is_allowed(name):
                continue
            candidates.append(name)
    deduped = []
    seen = set()
    for name in candidates:
        key = canonical_key(name)
        if key not in seen:
            seen.add(key)
            deduped.append(name)
    return deduped[:6]


def extract_seed_matches(text, seed_records):
    token_set = set(canonical_key(text).split())
    matches = []
    seen = set()
    seed_stop_tokens = {
        "cd47",
        "sirpa",
        "sirpalpha",
        "siglec",
        "siglec9",
        "protein",
        "ligand",
        "receptor",
        "variant",
        "peptide",
        "antibody",
        "mimetic",
        "glycomimetic",
        "ectodomain",
        "wt",
        "soluble",
        "construct",
        "fusion",
        "human",
    }
    for record in seed_records:
        candidate_name = sanitize_candidate_name(record["candidate_name"])
        if len(candidate_name) < 4:
            continue
        candidate_key = canonical_key(candidate_name)
        candidate_tokens = [token for token in candidate_key.split() if token]
        meaningful_tokens = [token for token in candidate_tokens if token not in seed_stop_tokens]
        exact_match = candidate_key and candidate_key in canonical_key(text)
        loose_match = bool(meaningful_tokens) and all(token in token_set for token in meaningful_tokens)
        if exact_match or loose_match:
            key = canonical_key(candidate_name)
            if key not in seen and candidate_is_allowed(candidate_name, seed_records):
                seen.add(key)
                matches.append(candidate_name)
    return matches


def prioritize_candidate_names(names):
    ordered = sorted(
        names,
        key=lambda name: (-len(canonical_key(name)), canonical_key(name), name.lower()),
    )
    kept = []
    seen = set()
    for name in ordered:
        if not candidate_is_allowed(name):
            continue
        key = canonical_key(name)
        if key in seen:
            continue
        if any(key != canonical_key(existing) and key in canonical_key(existing) for existing in kept):
            continue
        kept.append(name)
        seen.add(key)
    return kept


def article_link(article):
    source = article.get("source")
    article_id = article.get("id")
    if source and article_id:
        return f"https://europepmc.org/article/{source}/{article_id}"
    return ""


def load_history():
    if not HISTORY_PATH.exists():
        return {"seen_article_ids": [], "seen_lead_keys": [], "last_updated": None}
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:  # noqa: BLE001
        return {"seen_article_ids": [], "seen_lead_keys": [], "last_updated": None}
    if not isinstance(payload, dict):
        return {"seen_article_ids": [], "seen_lead_keys": [], "last_updated": None}
    payload.setdefault("seen_article_ids", [])
    payload.setdefault("seen_lead_keys", [])
    return payload


def save_history(payload):
    with open(HISTORY_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_json(path):
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:  # noqa: BLE001
        return None


def deepseek_research_enabled():
    return bool(DEEPSEEK_API_KEY) and AUTO_RESEARCH_LLM_ENABLED


def extract_json_array(text):
    stripped = (text or "").strip()
    if not stripped:
        return []
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1 or end < start:
        return []
    snippet = stripped[start : end + 1]
    try:
        parsed = json.loads(snippet)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def call_deepseek_research(messages, max_tokens=900):
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    req = request.Request(
        f"{DEEPSEEK_BASE_URL.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=120) as response:
        parsed = json.loads(response.read().decode("utf-8"))
    choices = parsed.get("choices") or []
    if not choices:
        return []
    message = choices[0].get("message") or {}
    return extract_json_array(message.get("content") or "")


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
    if any(term in text for term in ["surface", "coating", "interface", "biomaterial", "hemocompat", "blood-contacting"]):
        score += 4
    return min(score, 92)


def article_relevance_score(article_record, seed_records):
    text = f"{article_record.get('title', '')} {article_record.get('abstract', '')}".lower()
    title = (article_record.get("title", "") or "").lower()
    target = normalize_target_receptor(article_record.get("target_receptor"))
    rules = TARGET_DISCOVERY_TERMS.get(target, {"positive": set(), "negative": set()})

    score = 0
    if target == "Siglec-9" and ("siglec-9" in text or "siglec9" in text):
        score += 2
    if target == "SIRPa" and any(token in text for token in ["sirpalpha", "sirpa", "sirpα", "cd47"]):
        score += 2

    for token in rules["positive"]:
        if token in text:
            score += 2
        if token in title:
            score += 1

    for token in rules["negative"]:
        if token in text:
            score -= 2

    seed_matches = extract_seed_matches(text, seed_records)
    candidate_aliases = extract_candidate_names(text)
    score += min(8, len(seed_matches) * 3)
    score += min(4, len(candidate_aliases) * 2)

    if "review" in title or "comprehensive review" in title:
        score -= 3
    if "case report" in title:
        score -= 2

    return score


def build_article_record(article, target_receptor, query):
    record = {
        "id": f"{article.get('source', 'SRC')}-{article.get('id', '')}",
        "target_receptor": normalize_target_receptor(target_receptor),
        "query": query,
        "title": article.get("title", ""),
        "abstract": article.get("abstractText", ""),
        "author_string": article.get("authorString", ""),
        "journal_title": article.get("journalTitle", ""),
        "publication_date": article.get("firstPublicationDate") or article.get("pubYear"),
        "doi": article.get("doi", ""),
        "source_url": article_link(article),
        "article_id": article.get("id", ""),
    }
    return record


def build_leads_from_article(article_record, seed_records):
    text = f"{article_record['title']} {article_record['abstract']}"
    names = prioritize_candidate_names(extract_seed_matches(text, seed_records) + extract_candidate_names(text))
    leads = []
    seen = set()
    for name in names:
        key = canonical_key(name)
        if key in seen or not candidate_is_allowed(name, seed_records):
            continue
        seen.add(key)
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
                "article_id": article_record.get("article_id"),
                "source_method": "heuristic",
            }
        )
    return leads


def classify_known_seed(lead_name, seed_records):
    normalized = lead_name.lower()
    for record in seed_records:
        if record["candidate_name"].lower() == normalized:
            return True
    return False


def sanitize_lead_record(candidate_name, target_receptor, modality_guess, lead_score, rationale, article_record, source_method, seed_records=None):
    name = sanitize_candidate_name(candidate_name)
    if not candidate_is_allowed(name, seed_records):
        return None
    normalized_target = normalize_target_receptor(target_receptor) or normalize_target_receptor(article_record.get("target_receptor"))
    if normalized_target not in {"Siglec-9", "SIRPa"}:
        return None

    try:
        parsed_score = float(lead_score)
    except (TypeError, ValueError):
        parsed_score = 58.0

    return {
        "candidate_name": name,
        "target_receptor": normalized_target,
        "modality_guess": (modality_guess or "literature_lead").strip().lower(),
        "lead_score": max(20, min(95, round(parsed_score))),
        "lead_type": "literature_candidate_lead",
        "rationale": normalize_name(rationale or f"Recent literature mention in article: {article_record['title']}"),
        "publication_date": article_record.get("publication_date"),
        "source_title": article_record.get("title"),
        "source_url": article_record.get("source_url"),
        "article_id": article_record.get("article_id"),
        "source_method": source_method,
    }


def extract_llm_leads(article_records, seed_records):
    if not deepseek_research_enabled() or not article_records:
        return []

    compact_articles = [
        {
            "article_id": article.get("article_id"),
            "target_receptor": article.get("target_receptor"),
            "title": article.get("title"),
            "abstract": (article.get("abstract") or "")[:1800],
            "publication_date": article.get("publication_date"),
            "source_url": article.get("source_url"),
        }
        for article in article_records[:AUTO_RESEARCH_MAX_ARTICLES]
    ]

    system_prompt = (
        "You extract ECMO-relevant ligand discovery leads from recent paper metadata. "
        "Return only a JSON array. Each item must include: "
        "candidate_name, target_receptor, modality_guess, lead_score, article_id, rationale. "
        "Only include actual candidate ligands, peptides, glycomimetics, receptor-binding proteins, decoys, or antibodies relevant to Siglec-9 or SIRPalpha/CD47 screening. "
        "Do not include pathways, cargo molecules, signaling proteins, cell types, diseases, assays, or generic terms. "
        "Ignore names like STING, cGAMP, macrophage, neutrophil, cytokine, immune checkpoint, receptor, ligand, agonist, and similar generic biology terms. "
        "Prefer candidates explicitly named in the title or abstract. "
        "lead_score should be 0-100 and reflect how promising the candidate seems for follow-up triage."
    )
    user_prompt = json.dumps({"articles": compact_articles}, ensure_ascii=False)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    extracted = call_deepseek_research(messages, max_tokens=1100)
    leads = []
    article_index = {article.get("article_id"): article for article in article_records}
    for item in extracted:
        if not isinstance(item, dict):
            continue
        article = article_index.get(str(item.get("article_id") or "").strip())
        if not article:
            continue
        lead = sanitize_lead_record(
            item.get("candidate_name"),
            item.get("target_receptor") or article.get("target_receptor"),
            item.get("modality_guess"),
            item.get("lead_score"),
            item.get("rationale"),
            article,
            "deepseek",
            seed_records,
        )
        if lead:
            leads.append(lead)
    return leads


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
        "evidence_summary": f"{lead['rationale']} ({discovery_status.replace('_', ' ')}, {lead.get('source_method', 'heuristic')} extraction)",
        "source_urls": [lead["source_url"]] if lead.get("source_url") else [],
        "discovery_status": discovery_status,
        "lead_score": lead["lead_score"],
        "publication_date": lead.get("publication_date"),
        "source_title": lead.get("source_title"),
        "source_method": lead.get("source_method", "heuristic"),
        "article_id": lead.get("article_id"),
        "is_new": bool(lead.get("is_new")),
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


def lead_history_key(lead):
    return f"{normalize_target_receptor(lead.get('target_receptor'))}|{canonical_key(lead.get('candidate_name', ''))}"


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def refresh_research_outputs():
    ensure_outputs()
    seed_records = load_seed_records(SEED_PATH)
    existing_status = load_json(OUTPUTS / "research_status.json") or {}
    existing_articles_payload = load_json(OUTPUTS / "research_articles.json") or {}
    existing_leads_payload = load_json(OUTPUTS / "research_leads.json") or {}
    existing_autonomous_payload = load_json(OUTPUTS / "autonomous_ranking_results.json") or {}
    history = load_history()
    seen_article_ids = set(history.get("seen_article_ids") or [])
    seen_lead_keys = set(history.get("seen_lead_keys") or [])
    fetched_articles = []
    relevant_articles = []
    seen_fetched_article_ids = set()
    seen_relevant_article_ids = set()
    heuristic_leads = []
    llm_leads = []
    errors = []
    query_results = []

    for entry in SEARCH_QUERIES:
        query_articles = []
        try:
            payload = fetch_europe_pmc_results(entry["query"])
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:200]
            errors.append(f"{entry['target_receptor']}: Europe PMC HTTP {exc.code} - {detail}")
            query_results.append({"target_receptor": entry["target_receptor"], "ok": False, "error": f"HTTP {exc.code}"})
            continue
        except error.URLError as exc:
            errors.append(f"{entry['target_receptor']}: Europe PMC network error - {exc.reason}")
            query_results.append({"target_receptor": entry["target_receptor"], "ok": False, "error": str(exc.reason)})
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{entry['target_receptor']}: literature fetch failed - {exc}")
            query_results.append({"target_receptor": entry["target_receptor"], "ok": False, "error": str(exc)})
            continue

        for result in payload.get("resultList", {}).get("result", []):
            article_record = build_article_record(result, entry["target_receptor"], entry["query"])
            article_record["relevance_score"] = article_relevance_score(article_record, seed_records)
            article_key = article_record.get("id") or f"{article_record.get('title', '')}|{article_record.get('publication_date', '')}"
            if article_key not in seen_fetched_article_ids:
                fetched_articles.append(article_record)
                seen_fetched_article_ids.add(article_key)
            query_articles.append(article_record)
            if article_record["relevance_score"] >= 2 and article_key not in seen_relevant_article_ids:
                relevant_articles.append(article_record)
                seen_relevant_article_ids.add(article_key)
                heuristic_leads.extend(build_leads_from_article(article_record, seed_records))

        query_results.append(
            {
                "target_receptor": entry["target_receptor"],
                "ok": True,
                "article_count": len(query_articles),
                "relevant_article_count": sum(1 for article in query_articles if article.get("relevance_score", 0) >= 2),
            }
        )

        llm_query_articles = [article for article in query_articles if article.get("relevance_score", 0) >= 1]
        if deepseek_research_enabled() and llm_query_articles:
            try:
                llm_leads.extend(extract_llm_leads(llm_query_articles, seed_records))
            except error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:200]
                errors.append(f"{entry['target_receptor']}: DeepSeek HTTP {exc.code} - {detail}")
            except error.URLError as exc:
                errors.append(f"{entry['target_receptor']}: DeepSeek network error - {exc.reason}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{entry['target_receptor']}: DeepSeek extraction failed - {exc}")

    successful_queries = [result for result in query_results if result.get("ok")]

    deduped_leads = dedupe_leads(heuristic_leads + llm_leads)
    new_articles = [article for article in fetched_articles if article.get("id") not in seen_article_ids]
    new_leads = [lead for lead in deduped_leads if lead_history_key(lead) not in seen_lead_keys]
    for lead in deduped_leads:
        lead["is_new"] = lead_history_key(lead) not in seen_lead_keys
    autonomous_candidates = [build_candidate_from_lead(lead, seed_records) for lead in deduped_leads]
    autonomous_ranking = rank_records(seed_records, autonomous_candidates) if autonomous_candidates else {"models": {}, "metrics": {}, "ranked": []}
    candidate_index = {candidate["id"]: candidate for candidate in autonomous_candidates}
    for row in autonomous_ranking.get("ranked", []):
        candidate = candidate_index.get(row["id"], {})
        row["lead_score"] = candidate.get("lead_score")
        row["discovery_status"] = candidate.get("discovery_status")
        row["publication_date"] = candidate.get("publication_date")
        row["source_title"] = candidate.get("source_title")
        row["source_method"] = candidate.get("source_method")
        row["is_new"] = candidate.get("is_new")

    attempted_at = datetime.now(timezone.utc).isoformat()

    if not successful_queries and errors:
        cached_articles = existing_articles_payload.get("articles") or []
        cached_relevant_articles = existing_articles_payload.get("relevant_articles") or []
        cached_leads = existing_leads_payload.get("leads") or []
        cached_ranking = existing_autonomous_payload if isinstance(existing_autonomous_payload, dict) else {}
        summary = {
            "last_updated": existing_status.get("last_updated"),
            "last_attempted_at": attempted_at,
            "last_successful_data_at": existing_status.get("last_updated"),
            "article_count": existing_status.get("article_count", len(cached_articles)),
            "relevant_article_count": existing_status.get("relevant_article_count", len(cached_relevant_articles)),
            "new_article_count": 0,
            "lead_count": existing_status.get("lead_count", len(cached_leads)),
            "new_lead_count": 0,
            "autonomous_ranked_count": len(cached_ranking.get("ranked", [])),
            "heuristic_lead_count": existing_status.get("heuristic_lead_count", 0),
            "llm_lead_count": existing_status.get("llm_lead_count", 0),
            "llm_enabled": deepseek_research_enabled(),
            "llm_provider": "deepseek" if deepseek_research_enabled() else None,
            "query_results": query_results,
            "errors": errors,
            "health": "warning" if cached_leads or cached_ranking.get("ranked") else "error",
            "queries": SEARCH_QUERIES,
            "new_article_titles": [],
            "new_lead_names": [],
            "using_cached_results": True,
        }
        write_json(OUTPUTS / "research_status.json", summary)
        return summary

    summary = {
        "last_updated": attempted_at,
        "last_attempted_at": attempted_at,
        "last_successful_data_at": attempted_at,
        "article_count": len(fetched_articles),
        "relevant_article_count": len(relevant_articles),
        "new_article_count": len(new_articles),
        "lead_count": len(deduped_leads),
        "new_lead_count": len(new_leads),
        "autonomous_ranked_count": len(autonomous_ranking.get("ranked", [])),
        "heuristic_lead_count": len(heuristic_leads),
        "llm_lead_count": len(llm_leads),
        "llm_enabled": deepseek_research_enabled(),
        "llm_provider": "deepseek" if deepseek_research_enabled() else None,
        "query_results": query_results,
        "errors": errors,
        "health": "ok" if not errors else ("warning" if deduped_leads else "error"),
        "queries": SEARCH_QUERIES,
        "new_article_titles": [article.get("title", "") for article in new_articles[:5]],
        "new_lead_names": [lead.get("candidate_name", "") for lead in new_leads[:5]],
        "using_cached_results": False,
    }

    write_json(OUTPUTS / "research_articles.json", {"last_updated": summary["last_updated"], "articles": fetched_articles, "relevant_articles": relevant_articles})
    write_json(OUTPUTS / "research_leads.json", {"last_updated": summary["last_updated"], "leads": deduped_leads})
    write_json(OUTPUTS / "autonomous_candidates.json", {"last_updated": summary["last_updated"], "candidates": autonomous_candidates})
    write_json(OUTPUTS / "autonomous_ranking_results.json", autonomous_ranking)
    write_markdown(OUTPUTS / "autonomous_ranking_report.md", autonomous_ranking, "outputs/autonomous_candidates.json")
    write_json(OUTPUTS / "research_status.json", summary)
    save_history(
        {
            "last_updated": summary["last_updated"],
            "seen_article_ids": [article.get("id") for article in fetched_articles if article.get("id")],
            "seen_lead_keys": [lead_history_key(lead) for lead in deduped_leads],
        }
    )
    return summary


if __name__ == "__main__":
    summary = refresh_research_outputs()
    print(json.dumps(summary, indent=2))
