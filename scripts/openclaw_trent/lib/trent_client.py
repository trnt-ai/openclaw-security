# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Licensed under the Trent AI Proprietary License.

"""Minimal Trent API client using stdlib only (no httpx, no third-party deps).

Handles:
- API key auth from TRENT_API_KEY env var
- Streaming SSE chat endpoint
- Presigned S3 upload (prepare + PUT)
"""

import json
import os
import urllib.error
import urllib.request

from openclaw_trent import __version__

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DEFAULT_CHAT_URL = "https://chat.trent.ai"
_DEFAULT_AGENT_URL = "https://api.trent.ai"


def _get_chat_url() -> str:
    return os.environ.get("TRENT_CHAT_API_URL") or _DEFAULT_CHAT_URL


def _get_agent_url() -> str:
    return os.environ.get("TRENT_AGENT_API_URL") or _DEFAULT_AGENT_URL


def _get_api_key() -> str | None:
    """Read API key from TRENT_API_KEY env var."""
    key = os.environ.get("TRENT_API_KEY", "").strip()
    return key if key else None


def _get_auth_header() -> str:
    key = _get_api_key()
    if key:
        return key
    raise RuntimeError("No Trent API key found. Set the TRENT_API_KEY environment variable.")


# ---------------------------------------------------------------------------
# Chat (streaming SSE)
# ---------------------------------------------------------------------------


def chat(
    message: str,
    context: str | None = None,
    thread_id: str | None = None,
    output_file: str | None = None,
) -> dict:
    """Send a chat message to Trent API using streaming SSE.

    Streams chunks to a temp file as they arrive so that partial results
    survive if the process is killed by a sandbox timeout. The file path
    is included in the response as ``output_file`` so the caller (or the
    agent) can read it back.

    Args:
        message: The chat message to send.
        context: Optional context string.
        thread_id: Optional thread ID for conversation continuity.
        output_file: Optional path to write streaming output to.
            Defaults to a temp file in /tmp.

    Returns:
        dict with keys: content, thread_id, output_file, error (optional).
    """
    import tempfile

    auth_header = _get_auth_header()

    payload = json.dumps(
        {
            "message": message,
            "context": context,
            "thread_id": thread_id,
            "stream": True,
            "client_info": {
                "client_type": "openclaw-skill",
                "client_version": __version__,
            },
        }
    ).encode()

    headers = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }

    req = urllib.request.Request(
        f"{_get_chat_url()}/v1/chat",
        data=payload,
        headers=headers,
        method="POST",
    )

    # Write chunks to a file as they arrive — survives sandbox SIGTERM
    out_path = output_file or tempfile.mktemp(prefix="trent_chat_", suffix=".json")
    content_chunks: list[str] = []
    returned_thread_id: str | None = thread_id

    try:
        with urllib.request.urlopen(req, timeout=300) as resp, open(out_path, "w") as out:
            for raw_line in resp:
                line = raw_line.decode("utf-8").rstrip("\r\n")
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    chunk = None
                    if "content" in data:
                        chunk = data["content"]
                    elif "delta" in data and "content" in data["delta"]:
                        chunk = data["delta"]["content"]
                    if chunk:
                        content_chunks.append(chunk)
                        out.write(chunk)
                        out.flush()
                    if "thread_id" in data:
                        returned_thread_id = data["thread_id"]
                except json.JSONDecodeError:
                    continue

            # Write final result as structured JSON
            result = {
                "content": "".join(content_chunks),
                "thread_id": returned_thread_id,
            }
            out.seek(0)
            out.truncate()
            out.write(json.dumps(result, indent=2))

    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        if e.code == 401:
            return {
                "content": "API key rejected (expired or revoked). "
                "Generate a new key at https://app.trent.ai.",
                "error": True,
                "output_file": out_path,
            }
        return {"content": f"API error {e.code}: {body}", "error": True, "output_file": out_path}

    except TimeoutError:
        return {
            "content": "Request timed out. Please try again.",
            "error": True,
            "output_file": out_path,
        }

    except Exception as e:
        return {"content": f"An error occurred: {e}", "error": True, "output_file": out_path}

    return {
        "content": "".join(content_chunks),
        "thread_id": returned_thread_id,
        "output_file": out_path,
    }


# ---------------------------------------------------------------------------
# Document upload (presigned S3)
# ---------------------------------------------------------------------------


def _api_request(method: str, endpoint: str, json_data: dict | None = None) -> dict:
    """Make an authenticated JSON request to the Trent agent API."""
    auth_header = _get_auth_header()
    url = f"{_get_agent_url()}/v1/humber-agent{endpoint}"
    payload = json.dumps(json_data).encode() if json_data is not None else None

    headers: dict[str, str] = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def prepare_document_upload(
    name: str,
    doc_type: str,
    doc_format: str,
    digest: str | None = None,
) -> dict:
    """Prepare a presigned S3 URL for document upload."""
    body: dict = {"name": name, "type": doc_type, "format": doc_format}
    if digest:
        body["digest"] = digest
    return _api_request("POST", "/documents/upload", json_data=body)


def upload_content_to_presigned_url(
    upload_url: str,
    content: bytes,
    content_type: str = "application/zip",
) -> None:
    """PUT content to a presigned S3 URL (no auth header — creds in query params)."""
    req = urllib.request.Request(
        upload_url,
        data=content,
        headers={"Content-Type": content_type},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=120):
            pass  # 2xx — success
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"S3 upload failed: HTTP {e.code} — {body}") from e
