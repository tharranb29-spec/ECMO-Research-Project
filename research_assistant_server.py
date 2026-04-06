#!/usr/bin/env python3

import base64
import hmac
import json
import mimetypes
import os
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib import error, request

from build_dashboard_bundle import main as build_dashboard_bundle_main
from research_autoupdater import refresh_research_outputs


ROOT = Path(__file__).resolve().parent
HOST = os.environ.get("ECMO_DASHBOARD_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT") or os.environ.get("ECMO_DASHBOARD_PORT", "8765"))
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai").strip().lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_REASONING_EFFORT = os.environ.get("OPENAI_REASONING_EFFORT", "medium")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
AUTO_RESEARCH_ENABLED = os.environ.get("AUTO_RESEARCH_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
AUTO_RESEARCH_INTERVAL_SECONDS = int(os.environ.get("AUTO_RESEARCH_INTERVAL_SECONDS", "3600"))
AUTO_RESEARCH_LLM_ENABLED = os.environ.get("AUTO_RESEARCH_LLM_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
AUTO_RESEARCH_RUNTIME_PATH = ROOT / "outputs" / "research_runtime_status.json"
MAX_JSON_BODY_BYTES = int(os.environ.get("ECMO_MAX_JSON_BODY_BYTES", "65536"))
MAX_QUESTION_CHARS = int(os.environ.get("ECMO_MAX_QUESTION_CHARS", "2000"))
MAX_EXTRA_CONTEXT_CHARS = int(os.environ.get("ECMO_MAX_EXTRA_CONTEXT_CHARS", "12000"))
CHAT_RATE_LIMIT_COUNT = int(os.environ.get("ECMO_CHAT_RATE_LIMIT_COUNT", "20"))
CHAT_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("ECMO_CHAT_RATE_LIMIT_WINDOW_SECONDS", "300"))
REFRESH_RATE_LIMIT_COUNT = int(os.environ.get("ECMO_REFRESH_RATE_LIMIT_COUNT", "6"))
REFRESH_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("ECMO_REFRESH_RATE_LIMIT_WINDOW_SECONDS", "3600"))
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("ECMO_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}
BASIC_AUTH_USER = os.environ.get("ECMO_BASIC_AUTH_USER", "").strip()
BASIC_AUTH_PASSWORD = os.environ.get("ECMO_BASIC_AUTH_PASSWORD", "")
BASIC_AUTH_ENABLED = bool(BASIC_AUTH_USER and BASIC_AUTH_PASSWORD)

STATIC_FILES = {
    "/": ROOT / "dashboard.html",
    "/dashboard.html": ROOT / "dashboard.html",
    "/dashboard.js": ROOT / "dashboard.js",
    "/protein-viewer.js": ROOT / "protein-viewer.js",
    "/structure-showcase.html": ROOT / "structure-showcase.html",
    "/dashboard-data.js": ROOT / "dashboard-data.js",
    "/dashboard-config.json": ROOT / "dashboard-config.json",
    "/assets/3Dmol-min.js": ROOT / "assets" / "3Dmol-min.js",
    "/assets/zju-ism-mark.svg": ROOT / "assets" / "zju-ism-mark.svg",
}

DATASET_PATHS = {
    "seed": ROOT / "outputs" / "seed_ranking_results.json",
    "custom": ROOT / "outputs" / "custom_results.json",
    "autonomous": ROOT / "outputs" / "autonomous_ranking_results.json",
}

RUNTIME_LOCK = threading.Lock()
RUNTIME_STATE_GUARD = threading.Lock()
RATE_LIMIT_GUARD = threading.Lock()
RATE_LIMIT_BUCKETS = defaultdict(list)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "SAMEORIGIN",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'self'"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def latest_research_status():
    return read_json(ROOT / "outputs" / "research_status.json") or {}


def base_runtime_state():
    last_success = (latest_research_status() or {}).get("last_updated")
    next_run = None
    if last_success:
        dt = parse_iso_datetime(last_success)
        if dt is not None:
            next_run = (dt + timedelta(seconds=AUTO_RESEARCH_INTERVAL_SECONDS)).isoformat()
    return {
        "in_progress": False,
        "last_started_at": None,
        "last_finished_at": None,
        "last_success_at": last_success,
        "last_error": None,
        "last_trigger": None,
        "next_run_at": next_run,
        "interval_seconds": AUTO_RESEARCH_INTERVAL_SECONDS,
        "llm_enabled": AUTO_RESEARCH_LLM_ENABLED and bool(DEEPSEEK_API_KEY),
        "llm_provider": "deepseek" if AUTO_RESEARCH_LLM_ENABLED and bool(DEEPSEEK_API_KEY) else None,
        "auto_research_enabled": AUTO_RESEARCH_ENABLED,
    }


def load_runtime_state():
    state = base_runtime_state()
    persisted = read_json(AUTO_RESEARCH_RUNTIME_PATH) or {}
    if isinstance(persisted, dict):
        state.update(persisted)
    return state


RUNTIME_STATE = load_runtime_state()


def persist_runtime_state():
    write_json(AUTO_RESEARCH_RUNTIME_PATH, RUNTIME_STATE)


def update_runtime_state(**updates):
    with RUNTIME_STATE_GUARD:
        RUNTIME_STATE.update(updates)
        persist_runtime_state()
        return dict(RUNTIME_STATE)


def runtime_state_snapshot():
    with RUNTIME_STATE_GUARD:
        snapshot = dict(RUNTIME_STATE)
    snapshot["interval_seconds"] = AUTO_RESEARCH_INTERVAL_SECONDS
    snapshot["llm_enabled"] = AUTO_RESEARCH_LLM_ENABLED and bool(DEEPSEEK_API_KEY)
    snapshot["llm_provider"] = "deepseek" if AUTO_RESEARCH_LLM_ENABLED and bool(DEEPSEEK_API_KEY) else None
    snapshot["auto_research_enabled"] = AUTO_RESEARCH_ENABLED
    return snapshot


def load_bundle():
    return {
        "config": read_json(ROOT / "dashboard-config.json") or {},
        "seed": read_json(DATASET_PATHS["seed"]),
        "custom": read_json(DATASET_PATHS["custom"]),
        "autonomous": read_json(DATASET_PATHS["autonomous"]),
        "research_leads": read_json(ROOT / "outputs" / "research_leads.json"),
        "research_status": latest_research_status(),
        "research_runtime": runtime_state_snapshot(),
    }

def fetch_pdb_text(pdb_id):
    clean = "".join(ch for ch in (pdb_id or "").upper() if ch.isalnum())
    if len(clean) != 4:
        raise ValueError("Invalid PDB id.")

    cache_dir = ROOT / "outputs" / "structures"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{clean}.pdb"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    remote_url = f"https://files.rcsb.org/download/{clean}.pdb"
    req = request.Request(remote_url, headers={"User-Agent": "ECMO-Dashboard/1.0"})
    try:
        with request.urlopen(req, timeout=45) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"RCSB returned {exc.code} for {clean}: {detail[:200]}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Unable to fetch structure {clean} from RCSB: {exc.reason}") from exc

    cache_path.write_text(body, encoding="utf-8")
    return body


def extract_response_text(payload):
    if isinstance(payload, dict):
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        output = payload.get("output", [])
        chunks = []
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
        if chunks:
            return "\n".join(chunks)

    return "The model returned a response, but the text could not be parsed."


def build_context(dataset_key):
    bundle = load_bundle()
    config = bundle.get("config") or {}
    dataset = bundle.get(dataset_key) or {}
    ranked = dataset.get("ranked") or []
    metrics = dataset.get("metrics") or {}

    context = {
        "project": {
            "english_title": config.get("english_title"),
            "chinese_title": config.get("chinese_title"),
            "institution_name": config.get("institution_name"),
            "program_name": config.get("program_name"),
        },
        "dataset_key": dataset_key,
        "metrics": metrics,
        "ranked": ranked[:20],
    }
    return context


def build_messages(dataset_key, question, extra_context, history):
    context = build_context(dataset_key)
    system_prompt = (
        "You are a research assistant for an ECMO biomaterials project. "
        "Your job is to help explain ligand ranking results, compare candidates, reason over pasted new context, "
        "and answer broader project questions in a scientifically careful way. "
        "You must clearly distinguish between: "
        "(1) facts from the provided ranked dataset, "
        "(2) inferences from the provided context, and "
        "(3) general scientific guidance. "
        "Do not claim experiments were performed unless they appear in the provided context. "
        "If the user asks something the dataset cannot support, say so clearly and then answer as a reasoned hypothesis. "
        "Format answers cleanly for an on-page chat interface: prefer short headings, short paragraphs, and simple bullet or numbered lists. "
        "Do not use markdown tables, raw HTML tags such as <br>, or code fences unless the user explicitly asks for them."
    )

    user_context = {
        "dashboard_context": context,
        "extra_user_context": extra_context or "",
        "question": question,
    }

    messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": system_prompt}],
        }
    ]

    trimmed_history = history[-8:] if isinstance(history, list) else []
    for item in trimmed_history:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
            continue
        messages.append(
            {
                "role": role,
                "content": [{"type": "input_text", "text": content.strip()}],
            }
        )

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": json.dumps(user_context, ensure_ascii=False, indent=2),
                }
            ],
        }
    )
    return messages


def build_chat_messages(dataset_key, question, extra_context, history):
    context = build_context(dataset_key)
    system_prompt = (
        "You are a research assistant for an ECMO biomaterials project. "
        "Help explain ligand ranking results, compare candidates, reason over pasted new context, "
        "and answer broader project questions in a scientifically careful way. "
        "Clearly distinguish between facts from the provided ranked dataset, inferences from the provided context, "
        "and general scientific guidance. "
        "Do not claim experiments were performed unless they appear in the provided context. "
        "If the user asks something the dataset cannot support, say so clearly and answer as a reasoned hypothesis. "
        "Format answers cleanly for an on-page chat interface: prefer short headings, short paragraphs, and simple bullet or numbered lists. "
        "Do not use markdown tables, raw HTML tags such as <br>, or code fences unless the user explicitly asks for them."
    )

    user_context = {
        "dashboard_context": context,
        "extra_user_context": extra_context or "",
        "question": question,
    }

    messages = [{"role": "system", "content": system_prompt}]
    trimmed_history = history[-8:] if isinstance(history, list) else []
    for item in trimmed_history:
        role = item.get("role")
        content = item.get("content")
        if role not in {"user", "assistant"} or not isinstance(content, str) or not content.strip():
            continue
        messages.append({"role": role, "content": content.strip()})
    messages.append({"role": "user", "content": json.dumps(user_context, ensure_ascii=False, indent=2)})
    return messages


def call_openai_responses(dataset_key, question, extra_context, history):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": OPENAI_MODEL,
        "reasoning": {"effort": OPENAI_REASONING_EFFORT},
        "max_output_tokens": 900,
        "input": build_messages(dataset_key, question, extra_context, history),
    }

    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error while calling the OpenAI API: {exc.reason}") from exc

    return {
        "answer": extract_response_text(parsed),
        "model": parsed.get("model", OPENAI_MODEL),
        "response_id": parsed.get("id"),
    }


def call_deepseek_chat(dataset_key, question, extra_context, history):
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("DEEPSEEK_API_KEY is not set.")

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": build_chat_messages(dataset_key, question, extra_context, history),
        "stream": False,
        "max_tokens": 900,
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

    try:
        with request.urlopen(req, timeout=120) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Network error while calling the DeepSeek API: {exc.reason}") from exc

    choices = parsed.get("choices") or []
    if not choices:
        raise RuntimeError("DeepSeek returned no completion choices.")
    message = choices[0].get("message") or {}
    answer = (message.get("content") or "").strip()
    if not answer:
        answer = "The model returned an empty answer."

    return {
        "answer": answer,
        "model": parsed.get("model", DEEPSEEK_MODEL),
        "response_id": parsed.get("id"),
    }


def provider_enabled():
    if AI_PROVIDER == "deepseek":
        return bool(DEEPSEEK_API_KEY)
    return bool(OPENAI_API_KEY)


def current_model_name():
    if AI_PROVIDER == "deepseek":
        return DEEPSEEK_MODEL
    return OPENAI_MODEL


def call_model(dataset_key, question, extra_context, history):
    if AI_PROVIDER == "deepseek":
        return call_deepseek_chat(dataset_key, question, extra_context, history)
    return call_openai_responses(dataset_key, question, extra_context, history)


def refresh_due_now():
    status = latest_research_status()
    last_updated = parse_iso_datetime(status.get("last_updated"))
    if last_updated is None:
        return True
    return (datetime.now(timezone.utc) - last_updated).total_seconds() >= AUTO_RESEARCH_INTERVAL_SECONDS


def queue_refresh(reason):
    with RUNTIME_STATE_GUARD:
        if RUNTIME_STATE.get("in_progress"):
            return False
        RUNTIME_STATE.update(
            {
                "in_progress": True,
                "last_trigger": reason,
                "last_error": None,
            }
        )
        persist_runtime_state()
    thread = threading.Thread(target=run_refresh_cycle, args=(reason,), daemon=True, name=f"auto-research-{reason}")
    thread.start()
    return True


def maybe_schedule_stale_refresh(reason):
    if not AUTO_RESEARCH_ENABLED:
        return False
    if not refresh_due_now():
        return False
    return queue_refresh(reason)


def normalized_origin(origin):
    return (origin or "").strip().rstrip("/")


def prune_rate_limit_bucket(entries, window_seconds, now=None):
    cutoff = (now or time.time()) - window_seconds
    while entries and entries[0] < cutoff:
        entries.pop(0)


def rate_limit_check(client_key, bucket_name, limit_count, window_seconds):
    now = time.time()
    key = f"{bucket_name}:{client_key}"
    with RATE_LIMIT_GUARD:
        entries = RATE_LIMIT_BUCKETS[key]
        prune_rate_limit_bucket(entries, window_seconds, now=now)
        if len(entries) >= limit_count:
            retry_after = max(1, int(window_seconds - (now - entries[0])))
            return False, retry_after
        entries.append(now)
    return True, 0


class Handler(BaseHTTPRequestHandler):
    server_version = "ECMODashboard"
    sys_version = ""

    def version_string(self):
        return self.server_version

    def _client_ip(self):
        forwarded = self.headers.get("CF-Connecting-IP") or self.headers.get("X-Forwarded-For") or self.headers.get("X-Real-IP")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if self.client_address:
            return self.client_address[0]
        return "unknown"

    def _request_origin(self):
        origin = self.headers.get("Origin")
        if origin:
            return normalized_origin(origin)

        referer = self.headers.get("Referer")
        if referer:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                return normalized_origin(f"{parsed.scheme}://{parsed.netloc}")
        return ""

    def _expected_origin(self):
        host = (self.headers.get("X-Forwarded-Host") or self.headers.get("Host") or "").strip()
        proto = (self.headers.get("X-Forwarded-Proto") or "http").strip()
        if not host:
            return ""
        return normalized_origin(f"{proto}://{host}")

    def _origin_allowed(self):
        request_origin = self._request_origin()
        if not request_origin:
            return True
        if request_origin == self._expected_origin():
            return True
        return request_origin in ALLOWED_ORIGINS

    def _is_authorized(self):
        if not BASIC_AUTH_ENABLED:
            return True
        header = self.headers.get("Authorization", "")
        if not header.startswith("Basic "):
            return False
        try:
            decoded = base64.b64decode(header.split(" ", 1)[1]).decode("utf-8")
        except Exception:  # noqa: BLE001
            return False
        username, separator, password = decoded.partition(":")
        if not separator:
            return False
        return hmac.compare_digest(username, BASIC_AUTH_USER) and hmac.compare_digest(password, BASIC_AUTH_PASSWORD)

    def _send_auth_challenge(self):
        body = json.dumps({"ok": False, "error": "Authentication required."}, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="ECMO Research Dashboard"')
        self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _cache_control_for_path(self, path):
        if path.startswith("/api/"):
            return "no-store"
        if path in {"/", "/dashboard.html", "/structure-showcase.html", "/dashboard.js", "/dashboard-data.js", "/dashboard-config.json"}:
            return "no-store"
        return "public, max-age=3600"

    def _send_common_headers(self, path, content_type, content_length):
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", self._cache_control_for_path(path))
        for header_name, header_value in SECURITY_HEADERS.items():
            self.send_header(header_name, header_value)

    def _send_json(self, payload, status=HTTPStatus.OK, method="GET"):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(body)

    def _send_file(self, url_path, path, method="GET"):
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        body = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(HTTPStatus.OK)
        self._send_common_headers(url_path, mime or "application/octet-stream", len(body))
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(body)

    def _send_error_json(self, status, message, extra=None, method="GET"):
        payload = {"ok": False, "error": message}
        if extra:
            payload.update(extra)
        self._send_json(payload, status=status, method=method)

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Invalid Content-Length header.")

        if length <= 0:
            return {}
        if length > MAX_JSON_BODY_BYTES:
            raise ValueError(f"Request body too large. Limit is {MAX_JSON_BODY_BYTES} bytes.")

        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body.") from exc

    def _enforce_rate_limit(self, bucket_name, limit_count, window_seconds):
        allowed, retry_after = rate_limit_check(self._client_ip(), bucket_name, limit_count, window_seconds)
        if allowed:
            return True
        body = json.dumps({"ok": False, "error": "Rate limit exceeded."}, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.TOO_MANY_REQUESTS)
        self.send_header("Retry-After", str(retry_after))
        self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
        self.end_headers()
        self.wfile.write(body)
        return False

    def _handle_get_like(self, method="GET"):
        parsed = urlparse(self.path)

        if parsed.path == "/api/status":
            maybe_schedule_stale_refresh("status-poll")
            self._send_json(
                {
                    "ok": True,
                    "live_assistant_enabled": provider_enabled(),
                    "provider": AI_PROVIDER,
                    "model": current_model_name(),
                    "reasoning_effort": OPENAI_REASONING_EFFORT if AI_PROVIDER == "openai" else None,
                    "auto_research_enabled": AUTO_RESEARCH_ENABLED,
                    "auto_research_interval_seconds": AUTO_RESEARCH_INTERVAL_SECONDS,
                    "research_status": latest_research_status(),
                    "research_runtime": runtime_state_snapshot(),
                },
                method=method,
            )
            return
        if parsed.path == "/api/bundle":
            maybe_schedule_stale_refresh("bundle-poll")
            self._send_json({"ok": True, **load_bundle()}, method=method)
            return
        if parsed.path == "/api/structure":
            params = parse_qs(parsed.query or "")
            pdb_id = (params.get("pdb") or ["2JJS"])[0]
            try:
                body = fetch_pdb_text(pdb_id).encode("utf-8")
            except ValueError as exc:
                self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc), method=method)
                return
            except RuntimeError as exc:
                self._send_error_json(HTTPStatus.BAD_GATEWAY, str(exc), method=method)
                return

            self.send_response(HTTPStatus.OK)
            self._send_common_headers(parsed.path, "chemical/x-pdb; charset=utf-8", len(body))
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(body)
            return

        file_path = STATIC_FILES.get(parsed.path)
        if file_path is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        self._send_file(parsed.path, file_path, method=method)

    def do_GET(self):
        if not self._is_authorized():
            self._send_auth_challenge()
            return
        self._handle_get_like(method="GET")

    def do_HEAD(self):
        if not self._is_authorized():
            self.send_response(HTTPStatus.UNAUTHORIZED)
            self.send_header("WWW-Authenticate", 'Basic realm="ECMO Research Dashboard"')
            self._send_common_headers(self.path, "application/json; charset=utf-8", 0)
            self.end_headers()
            return
        self._handle_get_like(method="HEAD")

    def do_POST(self):
        if not self._is_authorized():
            self._send_auth_challenge()
            return
        if not self._origin_allowed():
            self._send_error_json(HTTPStatus.FORBIDDEN, "Origin not allowed.")
            return

        if self.path == "/api/research/refresh":
            if not AUTO_RESEARCH_ENABLED:
                self._send_error_json(HTTPStatus.BAD_REQUEST, "Autonomous research is disabled.")
                return
            if not self._enforce_rate_limit("refresh", REFRESH_RATE_LIMIT_COUNT, REFRESH_RATE_LIMIT_WINDOW_SECONDS):
                return
            started = queue_refresh("manual")
            self._send_json(
                {
                    "ok": True,
                    "started": started,
                    "message": "Manual refresh started." if started else "Refresh already running.",
                    "research_runtime": runtime_state_snapshot(),
                    "research_status": latest_research_status(),
                }
            )
            return

        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            payload = self._read_json_body()
        except ValueError as exc:
            status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE if "too large" in str(exc).lower() else HTTPStatus.BAD_REQUEST
            self._send_error_json(status, str(exc))
            return

        if not self._enforce_rate_limit("chat", CHAT_RATE_LIMIT_COUNT, CHAT_RATE_LIMIT_WINDOW_SECONDS):
            return

        dataset_key = payload.get("dataset", "seed")
        if dataset_key not in DATASET_PATHS:
            dataset_key = "seed"
        question = (payload.get("question") or "").strip()
        extra_context = (payload.get("extra_context") or "").strip()
        history = payload.get("history") or []

        if len(question) > MAX_QUESTION_CHARS:
            self._send_error_json(HTTPStatus.BAD_REQUEST, f"Question is too long. Limit is {MAX_QUESTION_CHARS} characters.")
            return
        if len(extra_context) > MAX_EXTRA_CONTEXT_CHARS:
            extra_context = extra_context[:MAX_EXTRA_CONTEXT_CHARS]
        if not isinstance(history, list):
            history = []
        history = history[-8:]

        if not question:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "Question is required.")
            return

        try:
            result = call_model(dataset_key, question, extra_context, history)
        except RuntimeError as exc:
            self._send_error_json(
                HTTPStatus.BAD_GATEWAY,
                str(exc),
                extra={
                    "live_assistant_enabled": provider_enabled(),
                    "provider": AI_PROVIDER,
                },
            )
            return

        self._send_json({"ok": True, "provider": AI_PROVIDER, **result})


def main():
    if AUTO_RESEARCH_ENABLED:
        start_background_updater()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving dashboard at http://{HOST}:{PORT}")
    print(f"Provider: {AI_PROVIDER}")
    print(f"Live assistant model: {current_model_name()}")
    if AUTO_RESEARCH_ENABLED:
        print(f"Auto research updater enabled every {AUTO_RESEARCH_INTERVAL_SECONDS} seconds")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


def run_refresh_cycle(reason="scheduled"):
    if not RUNTIME_LOCK.acquire(blocking=False):
        return False

    started_at = utc_now_iso()
    update_runtime_state(
        in_progress=True,
        last_started_at=started_at,
        last_trigger=reason,
        last_error=None,
    )

    try:
        summary = refresh_research_outputs()
        build_dashboard_bundle_main()
        finished_at = utc_now_iso()
        next_run = (datetime.now(timezone.utc) + timedelta(seconds=AUTO_RESEARCH_INTERVAL_SECONDS)).isoformat()
        update_runtime_state(
            in_progress=False,
            last_finished_at=finished_at,
            last_success_at=summary.get("last_updated"),
            last_error=None if not summary.get("errors") else " | ".join(summary.get("errors", [])[:3]),
            next_run_at=next_run,
        )
        print(
            f"[auto-research] updated leads={summary.get('lead_count', 0)} "
            f"articles={summary.get('article_count', 0)} "
            f"llm={summary.get('llm_lead_count', 0)} "
            f"at={summary.get('last_updated', '')}"
        )
        return True
    except Exception as exc:  # noqa: BLE001
        finished_at = utc_now_iso()
        next_run = (datetime.now(timezone.utc) + timedelta(seconds=AUTO_RESEARCH_INTERVAL_SECONDS)).isoformat()
        update_runtime_state(
            in_progress=False,
            last_finished_at=finished_at,
            last_error=str(exc),
            next_run_at=next_run,
        )
        print(f"[auto-research] refresh failed: {exc}")
        return False
    finally:
        RUNTIME_LOCK.release()


def start_background_updater():
    def loop():
        run_refresh_cycle("startup")
        while True:
            time.sleep(max(60, AUTO_RESEARCH_INTERVAL_SECONDS))
            run_refresh_cycle("scheduled")

    thread = threading.Thread(target=loop, daemon=True, name="auto-research-updater")
    thread.start()


if __name__ == "__main__":
    main()
