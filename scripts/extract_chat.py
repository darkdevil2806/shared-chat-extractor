#!/usr/bin/env python3
"""
Shared Chat Extractor
Extracts structured conversation data (metadata, message turns, code blocks)
from shared chat links (ChatGPT, Claude, Perplexity, etc.) or local HTML files.
Supports both legacy Next.js (__NEXT_DATA__) and modern React Router (turbo-stream / devalue) architectures.
"""

import sys
import os
import re
import json
import ssl
import argparse
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

__version__ = "1.5.0"

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

def fetch_html(url: str) -> str:
    """Fetch HTML content from a URL with a standard browser User-Agent."""
    ua = USER_AGENT
    if "gemini.google" in url or "share.gemini" in url:
        ua = "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": ua, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    )
    ctx = ssl._create_unverified_context()
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    try:
        with opener.open(req, timeout=25) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except Exception as e:
        # Fallback to curl if available
        try:
            import subprocess
            cmd = ["curl", "-sL", "-A", ua, url]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
            if res.returncode == 0 and res.stdout:
                return res.stdout.decode("utf-8", errors="replace")
        except Exception:
            pass
        raise e

def parse_devalue_stream(html: str) -> Optional[Dict[str, Any]]:
    """Decode React Router turbo-stream / devalue format used by modern ChatGPT."""
    prefix = 'window.__reactRouterContext.streamController.enqueue('
    pos = html.find(prefix)
    if pos == -1:
        return None
    
    start = pos + len(prefix)
    decoder = json.JSONDecoder()
    try:
        decoded_js_str, _ = decoder.raw_decode(html, start)
        turbo_data = json.loads(decoded_js_str)
    except Exception:
        return None

    if not isinstance(turbo_data, list):
        return None

    def unwrap(idx, memo=None):
        if memo is None:
            memo = {}
        if not isinstance(idx, int):
            return idx
        if idx < 0 or idx >= len(turbo_data):
            return idx
        if idx in memo:
            return memo[idx]
        
        val = turbo_data[idx]
        if isinstance(val, (int, float, str, bool)) or val is None:
            return val
        elif isinstance(val, list):
            res = []
            memo[idx] = res
            for item in val:
                res.append(unwrap(item, memo))
            return res
        elif isinstance(val, dict):
            res = {}
            memo[idx] = res
            for k, v in val.items():
                if k.startswith('_'):
                    try:
                        k_name = unwrap(int(k[1:]), memo)
                    except ValueError:
                        k_name = k
                else:
                    k_name = k
                res[str(k_name)] = unwrap(v, memo)
            return res
        return val

    # Search for data node containing linear_conversation or mapping
    data_node = None
    for i, item in enumerate(turbo_data):
        if isinstance(item, dict):
            unwrapped = unwrap(i)
            if isinstance(unwrapped, dict) and ('linear_conversation' in unwrapped or 'mapping' in unwrapped):
                data_node = unwrapped
                break

    if not data_node:
        return None

    title = data_node.get('title') or "Shared ChatGPT Conversation"
    created_at = data_node.get('create_time')
    model_name = data_node.get('default_model_slug') or "auto"
    
    messages = []
    seen_texts = set()
    linear = data_node.get('linear_conversation', [])

    for item in linear:
        if not isinstance(item, dict):
            continue
        msg = item.get('message')
        if not isinstance(msg, dict):
            continue
        role = msg.get('author', {}).get('role')
        if role not in ('user', 'assistant'):
            continue
        parts = msg.get('content', {}).get('parts', [])
        text_parts = []
        for p in parts:
            if isinstance(p, str):
                text_parts.append(p)
            elif isinstance(p, dict):
                if 'text' in p:
                    text_parts.append(p['text'])
                elif 'val' in p:
                    text_parts.append(str(p['val']))
        text = '\n'.join([t.strip() for t in text_parts if t.strip()]).strip()
        
        if not text or 'The output of this plugin was redacted' in text or text == 'Original custom instructions no longer available':
            continue
        
        # Deduplicate
        sig = (role, text[:80])
        if sig in seen_texts:
            continue
        seen_texts.add(sig)

        model = msg.get('metadata', {}).get('model_slug') or model_name
        messages.append({
            'role': role,
            'text': text,
            'model': model
        })

    if messages:
        return {
            'platform': 'ChatGPT',
            'title': title,
            'model': model_name,
            'created_at': created_at,
            'messages': messages
        }

    return None

def extract_next_data(html: str) -> Optional[Dict[str, Any]]:
    """Extract and parse the legacy __NEXT_DATA__ JSON script tag from HTML."""
    match = re.search(r'<script\s+id="__NEXT_DATA__"\s+type="application/json">([\s\S]*?)</script>', html)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            return None
    return None

def parse_chatgpt_next(html: str, next_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Parse ChatGPT share page from legacy __NEXT_DATA__."""
    if not next_data:
        return None
    title = "Shared ChatGPT Conversation"
    messages = []
    model_name = "Unknown Model"
    created_at = None

    page_props = next_data.get("props", {}).get("pageProps", {})
    server_resp = page_props.get("serverResponse", {})
    data = server_resp.get("data", {})
    
    if data.get("title"):
        title = data["title"]
    elif page_props.get("title"):
        title = page_props["title"]

    if data.get("create_time"):
        created_at = data["create_time"]
    
    linear = data.get("linear_conversation")
    mapping = data.get("mapping")

    if linear and isinstance(linear, list):
        for item in linear:
            msg = item.get("message")
            if not msg:
                continue
            role = msg.get("author", {}).get("role", "unknown")
            if role not in ("user", "assistant"):
                continue
            parts = msg.get("content", {}).get("parts", [])
            text_parts = [p if isinstance(p, str) else (p.get("text", "") if isinstance(p, dict) else "") for p in parts]
            text = "\n".join([t for t in text_parts if t]).strip()
            if text:
                model = msg.get("metadata", {}).get("model_slug")
                messages.append({
                    "role": role,
                    "text": text,
                    "model": model or model_name
                })
    elif mapping and isinstance(mapping, dict):
        for node_id, node in mapping.items():
            msg = node.get("message")
            if not msg:
                continue
            role = msg.get("author", {}).get("role", "unknown")
            if role not in ("user", "assistant"):
                continue
            parts = msg.get("content", {}).get("parts", [])
            text_parts = [p if isinstance(p, str) else (p.get("text", "") if isinstance(p, dict) else "") for p in parts]
            text = "\n".join([t for t in text_parts if t]).strip()
            if text:
                model = msg.get("metadata", {}).get("model_slug")
                messages.append({
                    "role": role,
                    "text": text,
                    "model": model or model_name
                })

    return {
        "platform": "ChatGPT",
        "title": title,
        "model": model_name,
        "created_at": created_at,
        "messages": messages
    } if messages else None

def parse_claude(html: str, next_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Parse Claude.ai share page from __NEXT_DATA__, API JSON, or rendered DOM."""
    messages = []
    title = "Shared Claude Conversation"

    # Strategy 1: Legacy __NEXT_DATA__ (older Claude)
    if next_data:
        props = next_data.get("props", {}).get("pageProps", {})
        chat = props.get("chat") or props.get("conversation") or {}
        if chat.get("name"):
            title = chat["name"]
        chat_msgs = chat.get("chat_messages", [])
        for m in chat_msgs:
            sender = m.get("sender", "human")
            role = "user" if sender == "human" else "assistant"
            text = m.get("text", "")
            if text:
                messages.append({
                    "role": role,
                    "text": text.strip()
                })

    # Strategy 2: Embedded API JSON response (chat_snapshots payload in page)
    if not messages:
        snapshot_match = re.search(
            r'"chat_messages"\s*:\s*\[', html
        )
        if snapshot_match:
            # Try to extract the full JSON object containing chat_messages
            # Search backwards for the opening brace
            start = html.rfind('{', 0, snapshot_match.start())
            if start != -1:
                decoder = json.JSONDecoder()
                try:
                    obj, _ = decoder.raw_decode(html, start)
                    if isinstance(obj, dict) and "chat_messages" in obj:
                        if obj.get("name"):
                            title = obj["name"]
                        for m in obj["chat_messages"]:
                            sender = m.get("sender", "human")
                            role = "user" if sender == "human" else "assistant"
                            # Handle both text and content array formats
                            text = m.get("text", "")
                            if not text and "content" in m:
                                content = m["content"]
                                if isinstance(content, list):
                                    text_parts = []
                                    for c in content:
                                        if isinstance(c, str):
                                            text_parts.append(c)
                                        elif isinstance(c, dict) and c.get("type") == "text":
                                            text_parts.append(c.get("text", ""))
                                    text = "\n".join(t for t in text_parts if t)
                                elif isinstance(content, str):
                                    text = content
                            if text and text.strip():
                                messages.append({
                                    "role": role,
                                    "text": text.strip()
                                })
                except (json.JSONDecodeError, ValueError):
                    pass

    # Strategy 3: Parse rendered DOM from browser-saved HTML
    if not messages:
        messages, title = _parse_claude_dom(html, title)

    is_claude = 'claude.ai' in html or 'anthropic' in html.lower()
    if messages or is_claude:
        return {
            "platform": "Claude",
            "title": title,
            "messages": messages
        }
    return None


def _parse_claude_dom(html: str, default_title: str) -> tuple:
    """Extract Claude conversation from browser-saved rendered DOM HTML."""
    messages = []
    title = default_title

    # Claude renders user messages in elements with data-testid="user-message"
    # and assistant messages in elements with data-testid="assistant-message"
    # or within divs with role-specific classes

    # Pattern 1: data-testid based (common in saved pages)
    user_msgs = re.findall(
        r'data-testid="user-message"[^>]*>([\s\S]*?)(?=<div[^>]*data-testid="|$)',
        html
    )
    assistant_msgs = re.findall(
        r'data-testid="assistant-message"[^>]*>([\s\S]*?)(?=<div[^>]*data-testid="|$)',
        html
    )

    if user_msgs or assistant_msgs:
        # Interleave user and assistant messages
        max_len = max(len(user_msgs), len(assistant_msgs))
        for i in range(max_len):
            if i < len(user_msgs):
                text = _strip_html(user_msgs[i])
                if text:
                    messages.append({"role": "user", "text": text})
            if i < len(assistant_msgs):
                text = _strip_html(assistant_msgs[i])
                if text:
                    messages.append({"role": "assistant", "text": text})
        return messages, title

    # Pattern 2: Detect "Human" / "Assistant" turn markers in rendered text
    # Claude often renders turns with visible "H" (human) and "A" (assistant) avatars
    turn_pattern = re.findall(
        r'<div[^>]*class="[^"]*(?:font-claude-message|prose|whitespace-pre)[^"]*"[^>]*>([\s\S]*?)</div>',
        html
    )
    if turn_pattern:
        for block in turn_pattern:
            text = _strip_html(block)
            if text and len(text) > 5:
                messages.append({
                    "role": "assistant",
                    "text": text
                })

    return messages, title


class _HTMLTextExtractor(HTMLParser):
    """Cleanly extract visible text from HTML without vulnerable regex tag stripping."""
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self._skip = True
        elif tag in ('br', 'p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr'):
            self.fed.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript'):
            self._skip = False
        elif tag in ('p', 'div', 'li', 'tr'):
            self.fed.append('\n')

    def handle_data(self, data):
        if not self._skip:
            self.fed.append(data)

    def get_text(self) -> str:
        text = ''.join(self.fed)
        return re.sub(r'\n{3,}', '\n\n', text).strip()


def _strip_html(html_fragment: str) -> str:
    """Safely remove HTML tags and normalize whitespace using HTMLParser."""
    parser = _HTMLTextExtractor()
    parser.feed(html_fragment)
    return parser.get_text()

def parse_gemini(html: str) -> Optional[Dict[str, Any]]:
    """Parse Gemini (Bard) share page."""
    html_lower = html.lower()
    if 'gemini.google' not in html_lower and 'share.gemini' not in html_lower and 'bardchatui' not in html_lower and 'gemini' not in html_lower:
        return None

    title = "Shared Gemini Conversation"
    og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if og_title:
        title = og_title.group(1).strip()
    else:
        t_match = re.search(r'<title>(.*?)</title>', html)
        if t_match:
            title = t_match.group(1).strip()

    title = re.sub(r'^\W*Gemini\s*[-–—]\s*', '', title).strip()
    if not title or title.lower() == 'gemini':
        title = "Shared Gemini Conversation"

    messages = []
    # If saved offline from browser with rendered DOM
    user_queries = re.findall(r'<(?:div|span|h2)[^>]*class="[^"]*(?:query-text|user-query)[^"]*"[^>]*>([\s\S]*?)</(?:div|span|h2)>', html)
    model_responses = re.findall(r'<(?:div|span)[^>]*class="[^"]*(?:response-text|model-response|markdown)[^"]*"[^>]*>([\s\S]*?)</(?:div|span)>', html)

    for i in range(max(len(user_queries), len(model_responses))):
        if i < len(user_queries):
            text = _strip_html(user_queries[i])
            if text:
                messages.append({"role": "user", "text": text})
        if i < len(model_responses):
            text = _strip_html(model_responses[i])
            if text:
                messages.append({"role": "assistant", "text": text})

    return {
        "platform": "Gemini",
        "title": title,
        "model": "gemini",
        "messages": messages
    }


def parse_perplexity(html: str) -> Optional[Dict[str, Any]]:
    """Parse Perplexity.ai search / share page."""
    html_lower = html.lower()
    if 'perplexity' not in html_lower and 'pplx' not in html_lower:
        return None

    title = "Shared Perplexity Conversation"
    og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if og_title:
        t = re.sub(r'\s*[-–|]\s*Perplexity.*$', '', og_title.group(1).strip(), flags=re.IGNORECASE).strip()
        if t and t.lower() != 'perplexity':
            title = t
    else:
        t_match = re.search(r'<title>(.*?)</title>', html)
        if t_match:
            t = re.sub(r'\s*[-–|]\s*Perplexity.*$', '', t_match.group(1).strip(), flags=re.IGNORECASE).strip()
            if t and t.lower() != 'perplexity':
                title = t

    messages = []
    # DOM parsing if saved offline
    user_queries = re.findall(r'<(?:h1|div|span)[^>]*class="[^"]*(?:query|header)[^"]*"[^>]*>([\s\S]*?)</(?:h1|div|span)>', html)
    model_answers = re.findall(r'<(?:div|span)[^>]*class="[^"]*(?:prose|answer)[^"]*"[^>]*>([\s\S]*?)</(?:div|span)>', html)

    for i in range(max(len(user_queries), len(model_answers))):
        if i < len(user_queries):
            text = _strip_html(user_queries[i])
            if text:
                messages.append({"role": "user", "text": text})
        if i < len(model_answers):
            text = _strip_html(model_answers[i])
            if text:
                messages.append({"role": "assistant", "text": text})

    return {
        "platform": "Perplexity",
        "title": title,
        "model": "perplexity",
        "messages": messages
    }


def parse_generic(html: str) -> Dict[str, Any]:
    """Generic text fallback."""
    title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    title = title_m.group(1).strip() if title_m else "Shared Conversation"

    clean_text = _strip_html(html)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    return {
        "platform": "Generic",
        "title": title,
        "raw_text_preview": clean_text[:2000],
        "messages": []
    }

def extract_code_blocks(text: str) -> List[Dict[str, str]]:
    """Extract code blocks with language from markdown text."""
    pattern = r'```([a-zA-Z0-9_\-\+]*)\n([\s\S]*?)```'
    matches = re.findall(pattern, text)
    blocks = []
    for lang, code in matches:
        blocks.append({
            "language": lang or "text",
            "code": code.strip()
        })
    return blocks

def format_as_markdown(data: Dict[str, Any]) -> str:
    """Format extracted conversation to clean Markdown."""
    lines = [
        f"# {data.get('title', 'Shared Conversation')}",
        f"**Platform:** {data.get('platform', 'Unknown')}  ",
    ]
    if data.get("model") and data["model"] != "Unknown Model":
        lines.append(f"**Model:** `{data['model']}`  ")
    lines.append("\n---\n")

    messages = data.get("messages", [])
    if not messages:
        lines.append("> ℹ️ **Notice:** No message turns could be extracted directly from this URL.")
        lines.append("> Many platforms (like Claude, Perplexity, or Gemini) render messages client-side via JavaScript or enforce Cloudflare bot checks.")
        lines.append(">\n> **To extract the full conversation:**")
        lines.append("> 1. Open the share link in your browser.")
        lines.append("> 2. Press `Cmd+S` (Mac) or `Ctrl+S` (Windows) and choose **Webpage, HTML Only**.")
        lines.append("> 3. Run the extractor on the saved file:")
        lines.append(">    ```bash")
        lines.append(">    python3 scripts/extract_chat.py path/to/saved_page.html")
        lines.append(">    ```\n")
        return "\n".join(lines)

    for i, msg in enumerate(messages, 1):
        role_title = "🧑 User" if msg["role"] == "user" else "🤖 Assistant"
        lines.append(f"### {role_title}\n")
        lines.append(msg["text"])
        lines.append("\n")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Extract structured conversation data from shared chat links or HTML files.")
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("source", help="URL or path to local HTML/JSON file")
    parser.add_argument("--format", choices=["json", "md"], default="md", help="Output format (default: md)")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    parser.add_argument("--extract-code", "-c", action="store_true", help="Extract code snippets to separate files")
    parser.add_argument("--code-dir", default="extracted_code", help="Directory to save code snippets if --extract-code is passed")
    parser.add_argument("--save-html", "-s", nargs="?", const="auto", default=None,
                        help="Save fetched HTML from URL to disk (optional filename, default: auto-named .html)")

    args = parser.parse_args()

    # Load HTML
    is_claude_url = False
    claude_share_id = None
    if args.source.startswith("http://") or args.source.startswith("https://"):
        # Detect Claude share URLs
        claude_match = re.match(r'https?://claude\.ai/share/([0-9a-fA-F-]+)', args.source)
        if claude_match:
            is_claude_url = True
            claude_share_id = claude_match.group(1)
        try:
            html = fetch_html(args.source)
        except Exception as e:
            sys.stderr.write(f"Error fetching URL {args.source}: {e}\n")
            sys.exit(1)

        if args.save_html:
            import time
            from urllib.parse import urlparse
            if args.save_html == "auto":
                domain = urlparse(args.source).netloc.replace("www.", "").split(".")[0]
                save_filename = f"{domain}_chat_{int(time.time())}.html"
            else:
                save_filename = args.save_html
            try:
                with open(save_filename, "w", encoding="utf-8") as f:
                    f.write(html)
                sys.stderr.write(f"Saved raw HTML to: {save_filename}\n")
            except Exception as err:
                sys.stderr.write(f"Warning: Failed to save HTML to {save_filename}: {err}\n")
    else:
        if not os.path.exists(args.source):
            sys.stderr.write(f"Source file not found: {args.source}\n")
            sys.exit(1)
        with open(args.source, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

    # 1. Try modern React Router stream first (ChatGPT 2025/2026)
    res = parse_devalue_stream(html)

    # 2. For Claude URLs, try the chat_snapshots API endpoint directly
    if not res and is_claude_url and claude_share_id:
        api_url = f"https://claude.ai/api/chat_snapshots/{claude_share_id}?rendering_mode=messages&render_all_tools=true"
        try:
            api_resp = fetch_html(api_url)
            api_data = json.loads(api_resp)
            if isinstance(api_data, dict) and "chat_messages" in api_data:
                title = api_data.get("name", "Shared Claude Conversation")
                messages = []
                for m in api_data["chat_messages"]:
                    sender = m.get("sender", "human")
                    role = "user" if sender == "human" else "assistant"
                    text = m.get("text", "")
                    if not text and "content" in m:
                        content = m["content"]
                        if isinstance(content, list):
                            text_parts = []
                            for c in content:
                                if isinstance(c, str):
                                    text_parts.append(c)
                                elif isinstance(c, dict) and c.get("type") == "text":
                                    text_parts.append(c.get("text", ""))
                            text = "\n".join(t for t in text_parts if t)
                    if text and text.strip():
                        messages.append({"role": role, "text": text.strip()})
                if messages:
                    res = {
                        "platform": "Claude",
                        "title": title,
                        "model": api_data.get("model", "claude"),
                        "messages": messages
                    }
        except Exception:
            pass  # Fall through to HTML parsing
    
    # 3. Try legacy Next.js data
    if not res:
        next_data = extract_next_data(html)
        res = parse_chatgpt_next(html, next_data)
        if not res:
            res = parse_claude(html, next_data)

    # 4. Try Gemini
    if not res or not res.get("messages"):
        gemini_res = parse_gemini(html)
        if gemini_res:
            res = gemini_res

    # 5. Try Perplexity
    if not res or not res.get("messages"):
        pplx_res = parse_perplexity(html)
        if pplx_res:
            res = pplx_res

    # 6. Fallback to generic
    if not res:
        res = parse_generic(html)

    # Optional code block extraction
    if args.extract_code:
        os.makedirs(args.code_dir, exist_ok=True)
        code_idx = 1
        for msg in res.get("messages", []):
            if msg["role"] == "assistant":
                blocks = extract_code_blocks(msg["text"])
                for b in blocks:
                    ext = b["language"].lower()
                    if ext in ("python", "py"): ext = "py"
                    elif ext in ("javascript", "js"): ext = "js"
                    elif ext in ("typescript", "ts"): ext = "ts"
                    elif ext in ("json",): ext = "json"
                    elif ext in ("bash", "sh", "shell"): ext = "sh"
                    elif ext in ("html",): ext = "html"
                    elif ext in ("css",): ext = "css"
                    elif ext in ("dart",): ext = "dart"
                    else: ext = "txt"
                    
                    filename = os.path.join(args.code_dir, f"snippet_{code_idx:02d}.{ext}")
                    with open(filename, "w", encoding="utf-8") as cf:
                        cf.write(b["code"] + "\n")
                    code_idx += 1
        sys.stderr.write(f"Extracted {code_idx - 1} code snippet(s) into {args.code_dir}/\n")

    if args.format == "json":
        output_str = json.dumps(res, indent=2, ensure_ascii=False)
    else:
        output_str = format_as_markdown(res)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"Extraction saved to {args.output}")
    else:
        print(output_str)

if __name__ == "__main__":
    main()
