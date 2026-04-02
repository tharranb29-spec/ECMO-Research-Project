#!/usr/bin/env python3

import json
import mimetypes
import os
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
AUTO_RESEARCH_INTERVAL_SECONDS = int(os.environ.get("AUTO_RESEARCH_INTERVAL_SECONDS", "21600"))

STATIC_FILES = {
    "/": ROOT / "dashboard.html",
    "/dashboard.html": ROOT / "dashboard.html",
    "/dashboard.js": ROOT / "dashboard.js",
    "/dashboard-data.js": ROOT / "dashboard-data.js",
    "/dashboard-config.json": ROOT / "dashboard-config.json",
    "/assets/zju-ism-mark.svg": ROOT / "assets" / "zju-ism-mark.svg",
}

DATASET_PATHS = {
    "seed": ROOT / "outputs" / "seed_ranking_results.json",
    "custom": ROOT / "outputs" / "custom_results.json",
    "autonomous": ROOT / "outputs" / "autonomous_ranking_results.json",
}


def read_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bundle():
    return {
        "config": read_json(ROOT / "dashboard-config.json") or {},
        "seed": read_json(DATASET_PATHS["seed"]),
        "custom": read_json(DATASET_PATHS["custom"]),
        "autonomous": read_json(DATASET_PATHS["autonomous"]),
    }


def latest_research_status():
    return read_json(ROOT / "outputs" / "research_status.json") or {}


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
        "If the user asks something the dataset cannot support, say so clearly and then answer as a reasoned hypothesis."
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
        "If the user asks something the dataset cannot support, say so clearly and answer as a reasoned hypothesis."
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


class Handler(BaseHTTPRequestHandler):
    server_version = "ECMODashboard/0.1"

    def _send_json(self, payload, status=HTTPStatus.OK):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path):
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return
        body = path.read_bytes()
        mime, _ = mimetypes.guess_type(str(path))
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json(
                {
                    "ok": True,
                    "live_assistant_enabled": provider_enabled(),
                    "provider": AI_PROVIDER,
                    "model": current_model_name(),
                    "reasoning_effort": OPENAI_REASONING_EFFORT if AI_PROVIDER == "openai" else None,
                    "auto_research_enabled": AUTO_RESEARCH_ENABLED,
                    "research_status": latest_research_status(),
                    "host": HOST,
                    "port": PORT,
                }
            )
            return
        if self.path == "/api/bundle":
            self._send_json({"ok": True, **load_bundle()})
            return

        file_path = STATIC_FILES.get(self.path)
        if file_path is None:
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return
        self._send_file(file_path)

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            self._send_json({"ok": False, "error": "Invalid JSON body."}, status=HTTPStatus.BAD_REQUEST)
            return

        dataset_key = payload.get("dataset", "seed")
        if dataset_key not in DATASET_PATHS:
            dataset_key = "seed"
        question = (payload.get("question") or "").strip()
        extra_context = (payload.get("extra_context") or "").strip()
        history = payload.get("history") or []

        if not question:
            self._send_json({"ok": False, "error": "Question is required."}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            result = call_model(dataset_key, question, extra_context, history)
        except RuntimeError as exc:
            self._send_json(
                {
                    "ok": False,
                    "error": str(exc),
                    "live_assistant_enabled": provider_enabled(),
                    "provider": AI_PROVIDER,
                },
                status=HTTPStatus.BAD_GATEWAY,
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


def run_refresh_cycle():
    try:
        summary = refresh_research_outputs()
        build_dashboard_bundle_main()
        print(
            f"[auto-research] updated leads={summary.get('lead_count', 0)} "
            f"articles={summary.get('article_count', 0)} "
            f"at={summary.get('last_updated', '')}"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[auto-research] refresh failed: {exc}")


def start_background_updater():
    def loop():
        run_refresh_cycle()
        while True:
            time.sleep(max(300, AUTO_RESEARCH_INTERVAL_SECONDS))
            run_refresh_cycle()

    thread = threading.Thread(target=loop, daemon=True, name="auto-research-updater")
    thread.start()


if __name__ == "__main__":
    main()
