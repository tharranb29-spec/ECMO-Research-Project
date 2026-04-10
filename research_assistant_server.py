#!/usr/bin/env python3

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from urllib import error, request

from build_dashboard_bundle import main as build_dashboard_bundle_main
from research_autoupdater import refresh_research_outputs


ROOT = Path(__file__).resolve().parent


def env_text(name, default=""):
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value)


def env_bool(name, default=False):
    raw = env_text(name, "1" if default else "0").strip().lower()
    return raw not in {"0", "false", "no", "off", ""}


def env_int(name, default):
    raw = env_text(name, str(default)).strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


HOST = os.environ.get("ECMO_DASHBOARD_HOST", "127.0.0.1")
PORT = env_int("PORT", env_int("ECMO_DASHBOARD_PORT", 8765))
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai").strip().lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_REASONING_EFFORT = os.environ.get("OPENAI_REASONING_EFFORT", "medium")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
AUTO_RESEARCH_ENABLED = env_bool("AUTO_RESEARCH_ENABLED", True)
AUTO_RESEARCH_INTERVAL_SECONDS = env_int("AUTO_RESEARCH_INTERVAL_SECONDS", 3600)
AUTO_RESEARCH_LLM_ENABLED = env_bool("AUTO_RESEARCH_LLM_ENABLED", True)
AUTO_RESEARCH_RUNTIME_PATH = ROOT / "outputs" / "research_runtime_status.json"
MAX_JSON_BODY_BYTES = env_int("ECMO_MAX_JSON_BODY_BYTES", 65536)
MAX_QUESTION_CHARS = env_int("ECMO_MAX_QUESTION_CHARS", 2000)
MAX_EXTRA_CONTEXT_CHARS = env_int("ECMO_MAX_EXTRA_CONTEXT_CHARS", 12000)
LOGIN_RATE_LIMIT_COUNT = env_int("ECMO_LOGIN_RATE_LIMIT_COUNT", 10)
LOGIN_RATE_LIMIT_WINDOW_SECONDS = env_int("ECMO_LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300)
CHAT_RATE_LIMIT_COUNT = env_int("ECMO_CHAT_RATE_LIMIT_COUNT", 20)
CHAT_RATE_LIMIT_WINDOW_SECONDS = env_int("ECMO_CHAT_RATE_LIMIT_WINDOW_SECONDS", 300)
REFRESH_RATE_LIMIT_COUNT = env_int("ECMO_REFRESH_RATE_LIMIT_COUNT", 6)
REFRESH_RATE_LIMIT_WINDOW_SECONDS = env_int("ECMO_REFRESH_RATE_LIMIT_WINDOW_SECONDS", 3600)
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("ECMO_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}
BASIC_AUTH_USER = os.environ.get("ECMO_BASIC_AUTH_USER", "").strip()
BASIC_AUTH_PASSWORD = os.environ.get("ECMO_BASIC_AUTH_PASSWORD", "")
BASIC_AUTH_ENABLED = bool(BASIC_AUTH_USER and BASIC_AUTH_PASSWORD)
APP_SESSION_SECRET = os.environ.get("ECMO_SESSION_SECRET", "") or DEEPSEEK_API_KEY or OPENAI_API_KEY or ""
APP_SESSION_TTL_HOURS = env_int("ECMO_SESSION_TTL_HOURS", 24)
APP_SESSION_COOKIE_NAME = "ecmo_session"

STATIC_FILES = {
    "/": ROOT / "dashboard.html",
    "/dashboard.html": ROOT / "dashboard.html",
    "/dashboard.js": ROOT / "dashboard.js",
    "/login.html": ROOT / "login.html",
    "/login.js": ROOT / "login.js",
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


def normalize_username(username):
    return str(username or "").strip().lower()


def format_display_name(username):
    cleaned = str(username or "").strip()
    if not cleaned:
        return "Research User"
    return cleaned


def register_login_user(target, username, password, display_name=None):
    canonical_username = str(username or "").strip()
    if not canonical_username or password is None or password == "":
        return
    target[normalize_username(canonical_username)] = {
        "username": canonical_username,
        "password": str(password),
        "display_name": str(display_name or format_display_name(canonical_username)).strip() or canonical_username,
    }


def load_login_users():
    users = {}
    raw_json = os.environ.get("ECMO_APP_LOGIN_USERS_JSON", "").strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, dict):
                for username, value in parsed.items():
                    if isinstance(value, dict):
                        register_login_user(
                            users,
                            username,
                            value.get("password", ""),
                            value.get("display_name") or value.get("name"),
                        )
                    else:
                        register_login_user(users, username, value)
            elif isinstance(parsed, list):
                for entry in parsed:
                    if not isinstance(entry, dict):
                        continue
                    register_login_user(
                        users,
                        entry.get("username", ""),
                        entry.get("password", ""),
                        entry.get("display_name") or entry.get("name"),
                    )
        except Exception:  # noqa: BLE001
            pass

    single_user = os.environ.get("ECMO_APP_LOGIN_USER", "").strip() or BASIC_AUTH_USER
    single_password = os.environ.get("ECMO_APP_LOGIN_PASSWORD", "") or BASIC_AUTH_PASSWORD
    if single_user and single_password:
        register_login_user(users, single_user, single_password)
    return users


APP_LOGIN_USERS = load_login_users()
APP_LOGIN_ENABLED = bool(APP_LOGIN_USERS and APP_SESSION_SECRET)


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
        "autonomous_promoted": read_json(ROOT / "outputs" / "autonomous_promoted_results.json"),
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


def safe_next_path(raw_value):
    if not raw_value:
        return "/"
    parsed = urlparse(raw_value)
    if parsed.scheme or parsed.netloc:
        return "/"
    path = parsed.path or "/"
    if not path.startswith("/"):
        return "/"
    if path == "/login.html":
        return "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{path}{query}"


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


def app_login_diagnostics():
    return {
        "enabled": APP_LOGIN_ENABLED,
        "user_count": len(APP_LOGIN_USERS),
        "session_secret_present": bool(APP_SESSION_SECRET),
        "multi_user_config_present": bool(os.environ.get("ECMO_APP_LOGIN_USERS_JSON", "").strip()),
        "using_single_user_fallback": bool(
            not os.environ.get("ECMO_APP_LOGIN_USERS_JSON", "").strip()
            and (
                os.environ.get("ECMO_APP_LOGIN_USER", "").strip()
                or os.environ.get("ECMO_APP_LOGIN_PASSWORD", "")
                or BASIC_AUTH_ENABLED
            )
        ),
        "using_api_key_secret_fallback": bool(
            not os.environ.get("ECMO_SESSION_SECRET", "")
            and bool(APP_SESSION_SECRET)
        ),
    }


def get_login_user_record(username):
    return APP_LOGIN_USERS.get(normalize_username(username))


def _urlsafe_b64encode(raw_bytes):
    return base64.urlsafe_b64encode(raw_bytes).decode("ascii").rstrip("=")


def _urlsafe_b64decode(encoded):
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def build_app_session_token(username):
    issued_at = int(time.time())
    expires_at = issued_at + max(1, APP_SESSION_TTL_HOURS) * 3600
    payload = {
        "u": username,
        "iat": issued_at,
        "exp": expires_at,
        "nonce": secrets.token_hex(8),
    }
    raw_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    secret = APP_SESSION_SECRET.encode("utf-8")
    signature = hmac.new(secret, raw_payload, hashlib.sha256).digest()
    return f"{_urlsafe_b64encode(raw_payload)}.{_urlsafe_b64encode(signature)}"


def parse_app_session_token(token):
    if not APP_LOGIN_ENABLED or not token or "." not in token:
        return None
    payload_part, signature_part = token.split(".", 1)
    try:
        raw_payload = _urlsafe_b64decode(payload_part)
        provided_signature = _urlsafe_b64decode(signature_part)
    except Exception:  # noqa: BLE001
        return None

    expected_signature = hmac.new(APP_SESSION_SECRET.encode("utf-8"), raw_payload, hashlib.sha256).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return None

    try:
        payload = json.loads(raw_payload.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None

    user_record = get_login_user_record(payload.get("u"))
    if not user_record:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload


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

    def _request_path(self):
        return urlparse(self.path).path

    def _is_api_request(self, path=None):
        return (path or self._request_path()).startswith("/api/")

    def _parse_cookies(self):
        cookies = {}
        raw_header = self.headers.get("Cookie", "")
        for entry in raw_header.split(";"):
            name, separator, value = entry.strip().partition("=")
            if separator and name:
                cookies[name] = value
        return cookies

    def _app_session_payload(self):
        if not APP_LOGIN_ENABLED:
            return None
        token = self._parse_cookies().get(APP_SESSION_COOKIE_NAME)
        return parse_app_session_token(token)

    def _session_user(self):
        payload = self._app_session_payload()
        if not payload:
            return None
        record = get_login_user_record(payload.get("u"))
        if not record:
            return None
        return {
            "username": record["username"],
            "display_name": record["display_name"],
        }

    def _is_secure_request(self):
        proto = (self.headers.get("X-Forwarded-Proto") or "").strip().lower()
        if proto:
            return proto == "https"
        return HOST not in {"127.0.0.1", "localhost"}

    def _is_authorized(self):
        if APP_LOGIN_ENABLED:
            return self._app_session_payload() is not None
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

    def _send_redirect(self, location, cookie_value=None, expires=False):
        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        if cookie_value is not None or expires:
            self.send_header("Set-Cookie", self._build_session_cookie(cookie_value or "", expires=expires))
        for header_name, header_value in SECURITY_HEADERS.items():
            self.send_header(header_name, header_value)
        self.end_headers()

    def _build_session_cookie(self, token, expires=False):
        parts = [f"{APP_SESSION_COOKIE_NAME}={token}", "Path=/", "HttpOnly", "SameSite=Lax"]
        if expires:
            parts.append("Max-Age=0")
            parts.append("Expires=Thu, 01 Jan 1970 00:00:00 GMT")
        else:
            parts.append(f"Max-Age={max(1, APP_SESSION_TTL_HOURS) * 3600}")
        if self._is_secure_request():
            parts.append("Secure")
        return "; ".join(parts)

    def _send_login_required(self, method="GET"):
        if APP_LOGIN_ENABLED:
            if self._is_api_request():
                extra = {"login_required": True, "auth_mode": "app-login"}
                body = json.dumps({"ok": False, "error": "Login required.", **extra}, ensure_ascii=False).encode("utf-8")
                self.send_response(HTTPStatus.UNAUTHORIZED)
                self.send_header("Set-Cookie", self._build_session_cookie("", expires=True))
                self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
                self.end_headers()
                if method != "HEAD":
                    self.wfile.write(body)
                return

            next_path = safe_next_path(self.path)
            self._send_redirect(f"/login.html?next={quote(next_path, safe='')}", expires=True)
            return

        body = json.dumps({"ok": False, "error": "Authentication required."}, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.send_header("WWW-Authenticate", 'Basic realm="ECMO Research Dashboard"')
        self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
        self.end_headers()
        if method != "HEAD":
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

        if parsed.path == "/healthz":
            self._send_json(
                {
                    "ok": True,
                    "service": "ecmo-research-dashboard",
                    "auth_mode": "app-login" if APP_LOGIN_ENABLED else ("basic" if BASIC_AUTH_ENABLED else "none"),
                },
                method=method,
            )
            return
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
                    "app_login_enabled": APP_LOGIN_ENABLED,
                    "auth_mode": "app-login" if APP_LOGIN_ENABLED else ("basic" if BASIC_AUTH_ENABLED else "none"),
                    "app_login_diagnostics": app_login_diagnostics(),
                    "session_user": self._session_user(),
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
        parsed = urlparse(self.path)
        allowed_paths = {"/healthz", "/login.html", "/login.js", "/assets/zju-ism-mark.svg"}
        if APP_LOGIN_ENABLED and parsed.path == "/login.html" and self._is_authorized():
            params = parse_qs(parsed.query or "")
            self._send_redirect(safe_next_path((params.get("next") or ["/"])[0]))
            return
        if parsed.path == "/healthz" or (APP_LOGIN_ENABLED and parsed.path in allowed_paths):
            self._handle_get_like(method="GET")
            return
        if not self._is_authorized():
            self._send_login_required(method="GET")
            return
        self._handle_get_like(method="GET")

    def do_HEAD(self):
        parsed = urlparse(self.path)
        allowed_paths = {"/healthz", "/login.html", "/login.js", "/assets/zju-ism-mark.svg"}
        if APP_LOGIN_ENABLED and parsed.path == "/login.html" and self._is_authorized():
            params = parse_qs(parsed.query or "")
            self._send_redirect(safe_next_path((params.get("next") or ["/"])[0]))
            return
        if parsed.path == "/healthz" or (APP_LOGIN_ENABLED and parsed.path in allowed_paths):
            self._handle_get_like(method="HEAD")
            return
        if not self._is_authorized():
            self._send_login_required(method="HEAD")
            return
        self._handle_get_like(method="HEAD")

    def do_POST(self):
        if not self._origin_allowed():
            self._send_error_json(HTTPStatus.FORBIDDEN, "Origin not allowed.")
            return

        if self.path == "/api/auth/login":
            if not APP_LOGIN_ENABLED:
                self._send_error_json(HTTPStatus.BAD_REQUEST, "Custom app login is not enabled.")
                return
            if not self._enforce_rate_limit("login", LOGIN_RATE_LIMIT_COUNT, LOGIN_RATE_LIMIT_WINDOW_SECONDS):
                return
            try:
                payload = self._read_json_body()
            except ValueError as exc:
                status = HTTPStatus.REQUEST_ENTITY_TOO_LARGE if "too large" in str(exc).lower() else HTTPStatus.BAD_REQUEST
                self._send_error_json(status, str(exc))
                return

            username = str(payload.get("username") or "").strip()
            password = str(payload.get("password") or "")
            next_path = safe_next_path(payload.get("next") or "/")
            user_record = get_login_user_record(username)
            if not user_record or not hmac.compare_digest(password, user_record["password"]):
                self._send_error_json(HTTPStatus.UNAUTHORIZED, "Invalid username or password.", extra={"login_required": True})
                return

            token = build_app_session_token(user_record["username"])
            body = json.dumps({"ok": True, "redirect_to": next_path}, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Set-Cookie", self._build_session_cookie(token))
            self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/auth/logout":
            body = json.dumps({"ok": True, "logged_out": True}, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            if APP_LOGIN_ENABLED:
                self.send_header("Set-Cookie", self._build_session_cookie("", expires=True))
            self._send_common_headers(self.path, "application/json; charset=utf-8", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        if not self._is_authorized():
            self._send_login_required(method="POST")
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
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving dashboard at http://{HOST}:{PORT}")
    print(f"Provider: {AI_PROVIDER}")
    print(f"Live assistant model: {current_model_name()}")
    if AUTO_RESEARCH_ENABLED:
        print(f"Auto research updater enabled every {AUTO_RESEARCH_INTERVAL_SECONDS} seconds")
        start_background_updater()
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
        time.sleep(5)
        run_refresh_cycle("startup")
        while True:
            time.sleep(max(60, AUTO_RESEARCH_INTERVAL_SECONDS))
            run_refresh_cycle("scheduled")

    thread = threading.Thread(target=loop, daemon=True, name="auto-research-updater")
    thread.start()


if __name__ == "__main__":
    main()
