---
name: shared-chat-extractor
description: >-
  Extracts structured conversation data (prompts, responses, metadata, code snippets)
  from shared chat links (ChatGPT, Claude, Perplexity) or local HTML files. Use when
  the user provides a shared chat URL, asks to extract/import a ChatGPT conversation,
  or wants to convert a web chat into Markdown/JSON or code files.
---

# Shared Chat Extractor

Extracts conversation turns, models, timestamps, and embedded code blocks from shared AI chat URLs or offline HTML dumps into clean Markdown, structured JSON, or extracted source code files.

## Extraction Procedure

### Step 1: Determine Input Type
Identify if the user provided:
1. A live URL (e.g. `https://chatgpt.com/share/...`, `https://claude.ai/share/...`)
2. A saved offline `.html` file path

### Step 2: Run Extraction Script
Run the bundled extractor script:

```bash
python3 scripts/extract_chat.py "<URL_OR_FILE>" [OPTIONS]
```

#### Available Options:
* `--format md`: (Default) Output clean, human-readable Markdown.
* `--format json`: Output structured JSON containing roles, messages, timestamps, and model slugs.
* `--output <path>`: Save extracted content to a target file.
* `--save-html [path]`: Automatically save the fetched raw HTML from a URL to a local file (e.g. `--save-html` or `--save-html dump.html`).
* `--extract-code`: Automatically extract all code snippets from assistant turns into separate source files with appropriate extensions (`.py`, `.js`, `.ts`, `.sh`, etc.).
* `--code-dir <dir>`: Target folder for extracted code snippets (default: `extracted_code/`).

### Step 3: Handling Anti-Bot / Cloudflare Blocks
If the provider blocks automated cURL/fetch (e.g. Cloudflare captcha or TLS fingerprinting):
1. Instruct the user to open the share link in their browser.
2. Save the webpage locally (`Cmd+S` / `Ctrl+S` as "HTML Only" or "Complete Webpage").
3. Run the script on the saved file:
   ```bash
   python3 scripts/extract_chat.py path/to/saved_chat.html --format md
   ```

## Reference Documentation
For details on provider-specific JSON schemas (`__NEXT_DATA__`) and message trees, see [Supported Providers](references/providers.md).
