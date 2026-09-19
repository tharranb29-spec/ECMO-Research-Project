#!/usr/bin/env python3
"""Evidence-gated Track 3 discovery prototype.

The workflow is intentionally shadow-only. GPT may retrieve and structure source
material, but deterministic gates decide whether records can enter an unordered
screening queue. No code in this module loads sealed outcomes, promotes a model,
or interprets docking as potency.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


ROOT = Path(__file__).resolve().parent
DEFAULT_STATE_PATH = ROOT / "outputs" / "track3_discovery_runtime.json"
STATE_PATH = Path(os.environ.get("TRACK3_DISCOVERY_STATE_PATH", DEFAULT_STATE_PATH))
STATE_LOCK = threading.Lock()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
MAX_MOLECULES = 12
ALLOWED_DISPOSITIONS = {"pending", "retain_for_review", "quarantine", "reject"}
CONTRACT_INPUTS = {
    "external_cohort_freeze": ROOT / "track3_a2a/outputs/v1.6/external_evidence/pass2_source_extraction/cohort_freeze_manifest.json",
    "development_model_report": ROOT / "track3_a2a/outputs/v1.6/model_reproduction/development_results.json",
    "dual_state_docking": ROOT / "track3_a2a/outputs/v1.4/docking/literature_pilot_2025_report.json",
    "tier_a_equilibration_gate": ROOT / "track3_a2a/outputs/v1.6/md/tier_a_equilibration/equilibration_gate_report.json",
}


CACHED_SOURCES = [
    {
        "source_id": "PMID:15163184",
        "title": "Study on affinity profile toward native human and bovine adenosine receptors of a series of 1,8-naphthyridine derivatives.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/15163184/",
        "doi": "10.1021/jm030977p",
        "pmid": "15163184",
        "source_type": "primary_publication_metadata",
        "retrieval_state": "cached",
        "full_text_state": "unavailable",
    },
    {
        "source_id": "PMID:11754583",
        "title": "7-Substituted pyrazolo-triazolo-pyrimidines as A2A adenosine receptor antagonists.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/11754583/",
        "doi": "10.1021/jm010924c",
        "pmid": "11754583",
        "source_type": "primary_publication_metadata",
        "retrieval_state": "cached",
        "full_text_state": "unavailable",
    },
    {
        "source_id": "PMID:18258439",
        "title": "A new generation of adenosine receptor antagonists: from di- to trisubstituted aminopyrimidines.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/18258439/",
        "doi": "10.1016/j.bmc.2008.01.013",
        "pmid": "18258439",
        "source_type": "primary_publication_metadata",
        "retrieval_state": "cached",
        "full_text_state": "unavailable",
    },
]

CACHED_MOLECULES = {
    "Cn1c(=O)c2c(ncn2C)n(C)c1=O": {
        "canonical_smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O",
        "scaffold_id": "demo:xanthine",
        "applicability": "outside_domain",
        "uncertainty": "high",
    },
    "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O": {
        "canonical_smiles": "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O",
        "scaffold_id": "demo:purine-ribose",
        "applicability": "inside_domain_simulated",
        "uncertainty": "high",
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def contract_status() -> dict:
    records = {}
    for name, path in CONTRACT_INPUTS.items():
        try:
            display_path = str(path.relative_to(ROOT))
        except ValueError:
            display_path = str(path)
        if not path.exists():
            records[name] = {"state": "unavailable", "path": display_path, "sha256": None}
            continue
        records[name] = {
            "state": "available",
            "path": display_path,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return records


def strip_json_fence(text: str) -> str:
    value = str(text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    return value.strip()


def extract_response_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts = []
    for item in payload.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                parts.append(content["text"])
    return "\n".join(parts)


class CachedDemoProvider:
    name = "cached_demo"

    def discover(self, query: str) -> dict:
        return {
            "provider": self.name,
            "state": "cached",
            "query": query,
            "sources": [dict(item) for item in CACHED_SOURCES],
            "extractions": [
                {
                    "source_id": item["source_id"],
                    "target": "ADORA2A",
                    "assay_context": "not resolved from cached metadata",
                    "molecule_mentions": [],
                    "evidence_quality": "quarantine",
                    "reason": "Primary full text and exact assay context are unavailable in the cached demo.",
                    "citation_url": item["url"],
                }
                for item in CACHED_SOURCES
            ],
            "notice": "Deterministic cached demonstration; no network or LLM call was made.",
        }


class OpenAIWebProvider:
    name = "openai_web_search"

    def __init__(self, api_key: str, model: str = OPENAI_MODEL):
        self.api_key = api_key
        self.model = model

    def discover(self, query: str) -> dict:
        prompt = (
            "Find up to five primary publications relevant to the user query. Return only a JSON object with "
            "two arrays: sources and extractions. Each source must contain source_id, title, url, doi, pmid, "
            "source_type, retrieval_state, and full_text_state. Each extraction must contain source_id, target, "
            "assay_context, molecule_mentions, evidence_quality, reason, and citation_url. Do not infer potency, "
            "efficacy, ordinal rank, or molecule identity. If exact source text does not support a field, use "
            "'unresolved'. The target is human wild-type ADORA2A. Query: " + query
        )
        payload = {
            "model": self.model,
            "tools": [{"type": "web_search_preview"}],
            "max_output_tokens": 2200,
            "input": prompt,
        }
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=120) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"OpenAI discovery error {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI discovery network error: {exc.reason}") from exc
        try:
            result = json.loads(strip_json_fence(extract_response_text(parsed)))
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("OpenAI discovery response was not valid structured JSON.") from exc
        if not isinstance(result.get("sources"), list) or not isinstance(result.get("extractions"), list):
            raise RuntimeError("OpenAI discovery response omitted required source or extraction arrays.")
        for source in result["sources"]:
            source["retrieval_state"] = "live"
        result.update({"provider": self.name, "state": "live", "query": query})
        return result


def rdkit_available() -> bool:
    try:
        import rdkit  # noqa: F401
    except ImportError:
        return False
    return True


def standardize_molecule(name: str, smiles: str, demo_mode: bool = False) -> dict:
    record = {
        "molecule_id": "mol:" + hashlib.sha256(f"{name}|{smiles}".encode("utf-8")).hexdigest()[:12],
        "name": name or "Unnamed molecule",
        "input_smiles": smiles,
        "canonical_smiles": None,
        "identity_hash": None,
        "scaffold_id": None,
        "standardization_state": "unavailable",
        "standardization_engine": None,
        "duplicate_of": None,
        "applicability": "unavailable",
        "uncertainty": "unavailable",
        "provisional_score": None,
        "score_state": "unavailable_no_serialized_ab_ridge",
        "screen_eligible": False,
        "eligibility_reasons": [],
        "state_label": "live",
    }
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            record["standardization_state"] = "invalid_smiles"
            record["eligibility_reasons"].append("SMILES could not be parsed by RDKit.")
            return record
        canonical = Chem.MolToSmiles(mol, canonical=True, isomericSmiles=True)
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=True)
        record.update({
            "canonical_smiles": canonical,
            "identity_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "scaffold_id": scaffold or "acyclic",
            "standardization_state": "standardized",
            "standardization_engine": "RDKit",
        })
    except ImportError:
        cached = CACHED_MOLECULES.get(smiles) if demo_mode else None
        if not cached:
            record["eligibility_reasons"].append("RDKit is unavailable; identity remains fail-closed.")
            return record
        canonical = cached["canonical_smiles"]
        record.update({
            "canonical_smiles": canonical,
            "identity_hash": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "scaffold_id": cached["scaffold_id"],
            "standardization_state": "cached_precomputed",
            "standardization_engine": "deterministic demo cache",
            "applicability": cached["applicability"],
            "uncertainty": cached["uncertainty"],
            "state_label": "simulated",
        })
    return record


def deduplicate(records: list[dict]) -> None:
    seen = {}
    for record in records:
        identity = record.get("identity_hash")
        if identity and identity in seen:
            record["duplicate_of"] = seen[identity]
            record["screen_eligible"] = False
            record["eligibility_reasons"].append("Duplicate standardized identity.")
        elif identity:
            seen[identity] = record["molecule_id"]


def evaluate_queue(records: list[dict], demo_mode: bool) -> dict:
    for record in records:
        if record["duplicate_of"]:
            continue
        if record["standardization_state"] not in {"standardized", "cached_precomputed"}:
            record["eligibility_reasons"].append("Standardized identity is required.")
            continue
        if record["applicability"] == "unavailable":
            record["eligibility_reasons"].append("Applicability assessment is unavailable.")
            continue
        if record["applicability"] == "outside_domain":
            record["eligibility_reasons"].append("Outside the provisional development domain.")
            continue
        if demo_mode and record["applicability"] == "inside_domain_simulated":
            record["screen_eligible"] = True
            record["eligibility_reasons"].append("Simulated demo eligibility only; not external admission.")
        else:
            record["eligibility_reasons"].append("No frozen production applicability adapter is integrated.")
    queue = [record for record in records if record["screen_eligible"]]
    scaffold_counts = {}
    for record in queue:
        scaffold = record["scaffold_id"]
        scaffold_counts[scaffold] = scaffold_counts.get(scaffold, 0) + 1
    return {
        "ordering": "unordered_composition_only",
        "count": len(queue),
        "scaffold_count": len(scaffold_counts),
        "scaffold_composition": scaffold_counts,
        "records": queue,
        "claim_limit": "Screen eligibility is not potency, rank, probability, cohort admission, or a certified hit.",
    }


def audit_chain(events: list[tuple[str, dict]]) -> list[dict]:
    chain = []
    previous = "GENESIS"
    for index, (event_type, details) in enumerate(events, start=1):
        entry = {
            "sequence": index,
            "event_type": event_type,
            "details": details,
            "previous_entry_hash": previous,
        }
        entry["entry_hash"] = canonical_hash(entry)
        previous = entry["entry_hash"]
        chain.append(entry)
    return chain


def select_provider(mode: str):
    if mode == "demo":
        return CachedDemoProvider(), None
    if OPENAI_API_KEY:
        return OpenAIWebProvider(OPENAI_API_KEY), None
    if mode == "live":
        return CachedDemoProvider(), "OPENAI_API_KEY is unavailable; fell back to cached demo."
    return CachedDemoProvider(), "Live GPT provider is unconfigured; using cached demo."


def run_workflow(query: str, molecules: list[dict] | None = None, provider_mode: str = "auto") -> dict:
    query = str(query or "human ADORA2A primary ligand evidence").strip()[:500]
    provider_mode = provider_mode if provider_mode in {"auto", "live", "demo"} else "auto"
    provider, fallback_reason = select_provider(provider_mode)
    discovery = provider.discover(query)
    demo_mode = discovery["state"] == "cached"
    if molecules is None:
        molecules = []
    if demo_mode and not molecules:
        molecules = [
            {"name": "Adenosine demo input", "smiles": "Nc1ncnc2c1ncn2[C@@H]1O[C@H](CO)[C@@H](O)[C@H]1O"},
            {"name": "Caffeine demo input", "smiles": "Cn1c(=O)c2c(ncn2C)n(C)c1=O"},
        ]
    normalized = []
    for raw in molecules[:MAX_MOLECULES]:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "Unnamed molecule").strip()[:120]
        smiles = str(raw.get("smiles") or "").strip()[:1000]
        if not smiles:
            continue
        normalized.append(standardize_molecule(name, smiles, demo_mode=demo_mode))
    deduplicate(normalized)
    queue = evaluate_queue(normalized, demo_mode)
    run_basis = {
        "query": query,
        "provider": discovery["provider"],
        "created_at_utc": utc_now(),
        "molecule_identity_hashes": [item.get("identity_hash") for item in normalized],
    }
    run_id = "shadow:" + canonical_hash(run_basis)[:16]
    events = [
        ("contract_resolution", {"inputs": contract_status(), "missing_inputs_fail_closed": True}),
        ("literature_query", {"query": query, "provider": discovery["provider"], "state": discovery["state"]}),
        ("sources_retrieved", {"count": len(discovery["sources"]), "citations_present": all(bool(x.get("url")) for x in discovery["sources"])}),
        ("structured_extraction", {"count": len(discovery["extractions"]), "llm_is_potency_oracle": False}),
        ("evidence_quality_gate", {"quarantined": sum(x.get("evidence_quality") == "quarantine" for x in discovery["extractions"]), "external_admission_changed": False}),
        ("identity_standardization", {"count": len(normalized), "rdkit_available": rdkit_available()}),
        ("applicability_queue", {"eligible_count": queue["count"], "ordering": queue["ordering"]}),
        ("promotion_firewall", {"served_model": None, "promotion_enabled": False, "tier_b_unlocked": False}),
    ]
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "created_at_utc": run_basis["created_at_utc"],
        "workflow_state": "cached_demo" if demo_mode else "live",
        "fallback_reason": fallback_reason,
        "query": query,
        "provider": {"name": discovery["provider"], "model": OPENAI_MODEL if not demo_mode else None, "api_key_exposed": False},
        "contract_inputs": contract_status(),
        "sources": discovery["sources"],
        "extractions": discovery["extractions"],
        "molecules": normalized,
        "screen_eligible_queue": queue,
        "human_disposition": {"status": "pending", "reviewer": None, "note": None, "updated_at_utc": None},
        "governance": {
            "autonomy_mode": "shadow_only",
            "external_outcomes_loaded": False,
            "external_membership_frozen": True,
            "served_model": None,
            "model_promotion_enabled": False,
            "tier_b_unlocked": False,
            "docking_role": "structural_evidence_only",
            "llm_role": "extraction_and_orchestration_only",
            "ordinal_ranking_presented": False,
            "per_position_probability_presented": False,
            "certified_hit_presented": False,
        },
        "audit_log": audit_chain(events),
    }
    save_state(payload)
    return payload


def save_state(payload: dict) -> None:
    with STATE_LOCK:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        temporary = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(STATE_PATH)


def load_state() -> dict | None:
    with STATE_LOCK:
        if not STATE_PATH.exists():
            return None
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def apply_disposition(run_id: str, status: str, reviewer: str, note: str = "") -> dict:
    if status not in ALLOWED_DISPOSITIONS - {"pending"}:
        raise ValueError("Disposition must be retain_for_review, quarantine, or reject.")
    reviewer = str(reviewer or "").strip()[:120]
    if not reviewer:
        raise ValueError("A named human reviewer is required.")
    with STATE_LOCK:
        if not STATE_PATH.exists():
            raise ValueError("No discovery run exists.")
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if payload.get("run_id") != run_id:
            raise ValueError("Run ID does not match the latest discovery run.")
        disposition = {"status": status, "reviewer": reviewer, "note": str(note or "")[:1000], "updated_at_utc": utc_now()}
        payload["human_disposition"] = disposition
        previous = payload["audit_log"][-1]["entry_hash"] if payload.get("audit_log") else "GENESIS"
        entry = {
            "sequence": len(payload.get("audit_log") or []) + 1,
            "event_type": "human_disposition",
            "details": disposition,
            "previous_entry_hash": previous,
        }
        entry["entry_hash"] = canonical_hash(entry)
        payload.setdefault("audit_log", []).append(entry)
        temporary = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(STATE_PATH)
        return payload


def capability_status() -> dict:
    return {
        "live_provider": "available" if OPENAI_API_KEY else "unavailable",
        "live_provider_name": "openai_web_search",
        "live_model": OPENAI_MODEL if OPENAI_API_KEY else None,
        "cached_demo": "available",
        "rdkit": "available" if rdkit_available() else "unavailable",
        "ab_ridge_scorer": "unavailable_no_serialized_model_artifact",
        "external_outcomes": "sealed",
        "model_promotion": "disabled",
        "tier_b": "locked",
        "autonomy": "shadow_only",
    }
