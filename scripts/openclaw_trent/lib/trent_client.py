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
import urllib.parse
import urllib.request

from openclaw_trent import __version__

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_DEFAULT_CHAT_URL = "https://chat.trent.ai"
_DEFAULT_AGENT_URL = "https://api.trent.ai"

_RENEWAL_URL_FALLBACK = "https://app.trent.ai/api-keys/renew?client=openclaw"
_EXPIRY_WARNING_WINDOW_SECONDS = 7 * 86400
_EXPIRY_WARNING_MAX_SECONDS = 365 * 86400


def _get_chat_url() -> str:
    return os.environ.get("TRENT_CHAT_API_URL") or _DEFAULT_CHAT_URL


def _get_agent_url() -> str:
    return os.environ.get("TRENT_AGENT_API_URL") or _DEFAULT_AGENT_URL


def _is_trusted_trent_url(url: str) -> bool:
    # Use urlparse so fragments/query strings/userinfo do not bypass the
    # host-allowlist via parser-confusion (e.g. "https://evil.com#@app.trent.ai").
    if not isinstance(url, str):
        return False
    url = url.strip()
    if not url.startswith("https://"):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
    except (ValueError, AttributeError):
        return False
    if parsed.scheme != "https":
        return False
    if parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if host == "localhost":
        return True
    return host == "trent.ai" or host.endswith(".trent.ai")


def _extract_expiration_warning(headers) -> str | None:
    """Read advisory API-key-expiry headers from a Trent API response.

    Advisory only; a TLS compromise allows false warnings — acceptable per
    TRE-1706 AppSec review item #5. Guidance URLs are constrained to the
    trent.ai domain to reduce phishing risk from MITM-injected values; if
    the server-provided URL is not on the allowlist, the renewal fallback
    constant is used instead.
    """
    if headers is None or not hasattr(headers, "get"):
        return None

    guidance = headers.get("X-Trent-API-Key-Expired-Key-Guidance")
    if guidance:
        renewal_url = guidance if _is_trusted_trent_url(guidance) else _RENEWAL_URL_FALLBACK
        return f"Trent API key has expired. Renew at: {renewal_url}"

    expires_in = headers.get("X-Trent-API-Key-Expires-In")
    if not expires_in:
        return None
    try:
        seconds = int(expires_in)
    except (TypeError, ValueError):
        return None
    if seconds <= 0 or seconds > _EXPIRY_WARNING_MAX_SECONDS:
        return None
    if seconds > _EXPIRY_WARNING_WINDOW_SECONDS:
        return None
    days = max(1, seconds // 86400)
    return f"Trent API key expires in {days} day(s). Renew at {_RENEWAL_URL_FALLBACK}"


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
    expiration_warning: str | None = None

    try:
        with urllib.request.urlopen(req, timeout=300) as resp, open(out_path, "w") as out:
            expiration_warning = _extract_expiration_warning(resp.headers)
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
        error_warning = _extract_expiration_warning(getattr(e, "headers", None))
        if e.code == 401:
            result = {
                "content": "API key rejected (expired or revoked). "
                "Generate a new key at https://app.trent.ai.",
                "error": True,
                "output_file": out_path,
            }
            if error_warning:
                result["expiration_warning"] = error_warning
            return result
        result = {"content": f"API error {e.code}: {body}", "error": True, "output_file": out_path}
        if error_warning:
            result["expiration_warning"] = error_warning
        return result

    except TimeoutError:
        return {
            "content": "Request timed out. Please try again.",
            "error": True,
            "output_file": out_path,
        }

    except Exception as e:
        return {"content": f"An error occurred: {e}", "error": True, "output_file": out_path}

    result = {
        "content": "".join(content_chunks),
        "thread_id": returned_thread_id,
        "output_file": out_path,
    }
    if expiration_warning:
        result["expiration_warning"] = expiration_warning
    return result


# ---------------------------------------------------------------------------
# Document upload (presigned S3)
# ---------------------------------------------------------------------------


def _api_request(method: str, endpoint: str, json_data: dict | None = None) -> dict:
    """Make an authenticated JSON request to the Trent agent API.

    Returns the parsed JSON response. When the server emits an advisory
    API-key-expiry header, the returned dict gains an ``expiration_warning``
    key so the OpenClaw caller can surface it without changing the call site.
    """
    auth_header = _get_auth_header()
    url = f"{_get_agent_url()}/v1/trent-agent{endpoint}"
    payload = json.dumps(json_data).encode() if json_data is not None else None

    headers: dict[str, str] = {
        "Authorization": auth_header,
        "Content-Type": "application/json",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        warning = _extract_expiration_warning(resp.headers)
        if warning and isinstance(data, dict):
            data["expiration_warning"] = warning
        return data


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
