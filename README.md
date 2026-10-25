<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python 3.8+">
  <a href="https://github.com/darkdevil2806/shared-chat-extractor/actions/workflows/ci.yml"><img src="https://github.com/darkdevil2806/shared-chat-extractor/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/dependencies-zero-brightgreen" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/platforms-ChatGPT%20%7C%20Claude%20%7C%20Gemini%20%7C%20Perplexity-orange" alt="Supported Platforms">
</p>

# 🗂️ Shared Chat Extractor

> A fast, lightweight, dependency-free tool to extract structured conversation turns, metadata, and code snippets from **ChatGPT**, **Claude**, **Google Gemini**, **Perplexity**, and other AI share links or offline HTML pages.

Converts AI conversation links into clean **Markdown**, structured **JSON**, or standalone **source code files**. Runs as a standalone CLI tool **and** as an official [Google Antigravity (AGY)](https://github.com/google/antigravity) skill.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔗 **Direct URL Extraction** | Paste a share link to automatically fetch and parse turns & metadata |
| 💾 **Automatic HTML Saving** | Save the raw fetched `.html` payload to disk with `--save-html` |
| 🌐 **Offline DOM Parsing** | Parse local `.html` files saved from browser sessions (`Cmd+S` / `Ctrl+S`) |
| 📝 **Markdown Output** | Clean, human-readable Markdown with role headers and formatting |
| 📊 **Structured JSON** | Full JSON with roles, model identifiers, timestamps, and metadata |
| 💻 **Code Extraction** | Automatically extract all code snippets into separate files (`.py`, `.js`, etc.) |
| 🔄 **Multi-Architecture Support** | Supports React Router turbo-stream, `__NEXT_DATA__`, OpenGraph negotiation, and DOM queries |
| 🔒 **Zero Dependencies** | Pure Python standard library (`urllib`, `re`, `json`, `ssl`) — nothing to install |

---

## 📦 Installation

### Option 1: Direct Global CLI Install (Recommended)
Install directly from GitHub via `pip` or `pipx`:

```bash
pip install git+https://github.com/darkdevil2806/shared-chat-extractor.git
# Or with pipx:
pipx install git+https://github.com/darkdevil2806/shared-chat-extractor.git
```
This adds the `shared-chat-extractor` command globally to your terminal!

### Option 2: Clone & Run (Zero Dependencies)
You can also run directly from source without installing anything:

```bash
git clone https://github.com/darkdevil2806/shared-chat-extractor.git
cd shared-chat-extractor
```

> **Requirements:** Python 3.8 or higher (uses only standard library modules).

---

## 🚀 Quick Start Examples

### 1. Extract Directly from a URL (Default Markdown)
```bash
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example"
```

### 2. Output as Structured JSON
```bash
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example" --format json
```

### 3. Save Markdown to a File
```bash
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example" --output chat.md
```

### 4. Save Raw HTML from the URL
```bash
# Auto-generate a timestamped filename (e.g. chatgpt_chat_1792676527.html)
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example" --save-html

# Or specify a custom output filename
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example" --save-html raw_chat.html
```

### 5. Extract Embedded Code Snippets into Files
```bash
python3 scripts/extract_chat.py "https://chatgpt.com/share/e/abc123-example" \
  --extract-code --code-dir my_snippets/
```

### 6. Parse an Offline / Browser-Saved HTML File
```bash
python3 scripts/extract_chat.py path/to/saved_chat.html --format md
```

---

## 🌐 Supported Platforms & Extraction Behavior

AI platforms deliver shared conversations using different web architectures:

| Platform | URL Pattern | Direct URL Extraction | Offline HTML (`Cmd+S`) | Details |
|----------|------------|-----------------------|------------------------|---------|
| **ChatGPT** | `chatgpt.com/share/*` |  **Full turns + model** |  Supported | Server-side rendered via React Router turbo-stream / devalue. |
| **Gemini** | `share.gemini.google/*`<br>`gemini.google.com/share/*` |  **Title + metadata** |  **Full turns** | Server negotiates OpenGraph title; turns load client-side via Google RPC. |
| **Claude** | `claude.ai/share/*` | ⚠️ **Title/Shell** |  **Full turns** | App shell is served; messages load via `/api/chat_snapshots/` behind Cloudflare. |
| **Perplexity** | `perplexity.ai/search/*` | ⚠️ **Title/Shell** |  **Full turns** | Single-page application root behind Cloudflare bot challenges. |
| **Generic** | Any URL / HTML file | ⚠️ **Text preview** | ⚠️ **Text preview** | Fallback text extractor strips scripts/styles and extracts body text. |

---

## 📖 Step-by-Step Tutorial

### Scenario A: Direct URL Extraction (ChatGPT & Server-Rendered Chats)
For platforms that embed conversation data directly into the initial page response:
1. Copy the share URL from the chat interface.
2. Run:
   ```bash
   python3 scripts/extract_chat.py "<URL>" --output conversation.md
   ```
3. The conversation is immediately extracted into clean Markdown with user/assistant roles.

---

### Scenario B: Client-Rendered SPAs & Cloudflare-Protected Links (Claude, Perplexity, Gemini)
When platforms load message turns dynamically in the browser or require human verification:
1. Open the share URL in your regular browser (Chrome, Safari, Firefox, Edge).
2. Wait for the conversation to finish loading on screen.
3. Press **Cmd+S** (macOS) or **Ctrl+S** (Windows/Linux).
4. In the save dialog, select **Webpage, HTML Only** (or complete webpage) and save to your disk (e.g. `saved_chat.html`).
5. Run the extractor on the saved file:
   ```bash
   python3 scripts/extract_chat.py saved_chat.html --output conversation.md
   ```
6. The extractor parses the rendered DOM structure and outputs the complete conversation.

---

### Scenario C: Extracting Source Code into Standalone Files
If an AI assistant provides code snippets in Python, JavaScript, TypeScript, Bash, etc., you can pull them directly into runnable files:
```bash
python3 scripts/extract_chat.py "https://chatgpt.com/share/..." --extract-code --code-dir code_output/
```
Output directory structure:
```
code_output/
├── snippet_01.py
├── snippet_02.js
├── snippet_03.sh
└── snippet_04.ts
```

---

## ⚙️ CLI Reference

```
usage: extract_chat.py [-h] [--format {json,md}] [--output OUTPUT]
                       [--extract-code] [--code-dir CODE_DIR]
                       [--save-html [SAVE_HTML]]
                       source

Extract structured conversation data from shared chat links or HTML files.

positional arguments:
  source                URL or path to local HTML/JSON file

options:
  -h, --help            Show help message and exit
  --format {json,md}    Output format: 'md' for Markdown, 'json' for JSON (default: md)
  --output, -o OUTPUT   Output file path (default: stdout)
  --extract-code, -c    Extract assistant code snippets into separate files
  --code-dir CODE_DIR   Directory for extracted code snippets (default: extracted_code/)
  --save-html, -s       Save fetched raw HTML from URL to disk (optional filename)
```

---

## 🤖 Using as a Google Antigravity (AGY) Skill

This repository can be imported directly as a skill for [Google Antigravity](https://github.com/google/antigravity):

```bash
# Global install (available across all projects):
cp -r shared-chat-extractor ~/.gemini/config/skills/

# Or workspace install (current project only):
cp -r shared-chat-extractor .gemini/skills/
```

Once installed, the AI assistant will automatically use the skill whenever you provide an AI share link or ask to extract conversation files.

---

## 🗂️ Project Structure

```
shared-chat-extractor/
├── SKILL.md              # Antigravity skill definition
├── README.md             # Complete documentation and tutorials
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # Contribution and development guidelines
├── .gitignore            # Git exclusion rules
├── scripts/
│   └── extract_chat.py   # Complete standalone extractor script
├── references/
│   └── providers.md      # Detailed payload and architecture notes
├── examples/
│   ├── sample_output.md  # Example Markdown output
│   └── sample_output.json# Example structured JSON output
└── .github/
    └── ISSUE_TEMPLATE.md # Bug report and feature request template
```

---

## 🔐 Privacy & Security

- **100% Local Processing:** Runs entirely on your local machine. No third-party relays or telemetry.
- **Zero Credentials:** No API keys, passwords, or personal accounts required.
- **Safe Scraping:** Follows standard web standards and does not attempt credential harvesting or security bypasses.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
