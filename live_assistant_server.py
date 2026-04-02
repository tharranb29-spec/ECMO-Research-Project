#!/usr/bin/env python3

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get("DASHBOARD_PORT", "8765"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_PROJECT = os.environ.get("OPENAI_PROJECT")
OPENAI_ORG = os.environ.get("OPENAI_ORGANIZATION")


def load_json(path):
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_dashboard_context(dataset_key):
    config = load_json(ROOT / "dashboard-config.json") or {}
    seed = load_json(ROOT / "outputs" / "seed_ranking_results.json")
    custom = load_json(ROOT / "outputs" / "custom_results.json")
    dataset = custom if dataset_key == "custom" else seed
    return {"config": config, "dataset_key": dataset_key, "dataset": dataset}


def build_messages(context, question, extra_context, history):
    cfg = context["config"]
    dataset = context["dataset"] or {}
    ranked = dataset.get("ranked", [])
    metrics = dataset.get("metrics", {})
    top_hits = ranked[:8]

    system_prompt = f"""
You are a conversational ECMO ligand research assistant embedded in a university project dashboard.

Project English title:
{cfg.get("english_title", "ECMO Ligand Ranking Dashboard")}

Project Chinese title:
{cfg.get("chinese_title", "")}

Your job:
- Answer broader project questions in clear research language.
- Use the supplied ranking results as current machine-generated evidence.
- Use any extra pasted user context as new provisional input.
- Distinguish between direct evidence from the ranking dataset and your inference.
- Do not invent wet-lab validation, docking values, or literature support that is not present.
- If the question goes beyond the available dashboard data, say so clearly and answer cautiously.
- When reasoning over new inputs, label the conclusion as provisional.
- Keep answers concise but useful for group discussion.
""".strip()

    dataset_summary = {
        "active_dataset": context["dataset_key"],
        "metrics": metrics,
        "top_ranked_candidates": top_hits,
        "candidate_count": len(ranked),
    }

    user_prompt = {
        "question": question,
        "extra_context": extra_context or "",
        "dashboard_dataset_summary": dataset_summary,
    }

    messages = [
        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]}
    ]

    for turn in history[-8:]:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        text = turn.get("text", "").strip()
        if text:
          messages.append({"role": role, "content": [{"type": "input_text", "text": text}]})

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": json.dumps(user_prompt, ensure_ascii=False, indent=2),
                }
            ],
        }
    )
    return messages


def call_openai(messages):
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    payload = {
        "model": OPENAI_MODEL,
        "reasoning": {"effort": "medium"},
        "input": messages,
    }

    request = Request(
        f"{OPENAI_BASE_URL.rstrip('/')}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            **({"OpenAI-Project": OPENAI_PROJECT} if OPENAI_PROJECT else {}),
            **({"OpenAI-Organization": OPENAI_ORG} if OPENAI_ORG else {}),
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"OpenAI API error {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


def extract_text(payload):
    if isinstance(payload, dict):
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()

        output = payload.get("output")
        if isinstance(output, list):
            parts = []
            for item in output:
                content = item.get("content", []) if isinstance(item, dict) else []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "output_text" and isinstance(block.get("text"), str):
                            parts.append(block["text"])
                        elif isinstance(block.get("text"), str):
                            parts.append(block["text"])
            text = "\n".join(part.strip() for part in parts if part and part.strip()).strip()
            if text:
                return text
    return "I could not extract a text answer from the model response."


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "live_assistant_ready": bool(OPENAI_API_KEY),
                    "model": OPENAI_MODEL,
                    "port": PORT,
                },
            )
            return
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
            return

        dataset_key = payload.get("dataset", "seed")
        question = (payload.get("question") or "").strip()
        extra_context = (payload.get("extra_context") or "").strip()
        history = payload.get("history") or []

        if not question:
            self._send_json(400, {"error": "Question is required"})
            return

        try:
            context = load_dashboard_context(dataset_key)
            messages = build_messages(context, question, extra_context, history)
            response_payload = call_openai(messages)
            answer = extract_text(response_payload)
            self._send_json(
                200,
                {
                    "answer": answer,
                    "model": OPENAI_MODEL,
                    "dataset": dataset_key,
                },
            )
        except Exception as exc:  # noqa: BLE001
            self._send_json(
                500,
                {
                    "error": str(exc),
                    "live_assistant_ready": bool(OPENAI_API_KEY),
                },
            )


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    print(f"Serving dashboard at http://127.0.0.1:{PORT}/dashboard.html")
    print(f"Live assistant model: {OPENAI_MODEL}")
    if not OPENAI_API_KEY:
        print("Warning: OPENAI_API_KEY is not set. The dashboard will load, but live chat will not work.", file=sys.stderr)
    server.serve_forever()


if __name__ == "__main__":
    main()
