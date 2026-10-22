# Supported Providers & Payload Formats

This document describes how conversation payloads are structured and extracted across different AI platforms.

---

## 1. ChatGPT (`https://chatgpt.com/share/<share-id>`)
* **Architecture**: Modern React Router (turbo-stream / devalue encoding) and legacy Next.js SSR (`__NEXT_DATA__`).
* **Payload Location**:
  * **Modern (Default)**: Embedded inside `window.__reactRouterContext.streamController.enqueue(...)`.
  * **Legacy**: Embedded in `<script id="__NEXT_DATA__" type="application/json">`.
* **Path**:
  * Devalue stream: Recursively unwrapped data dictionary containing `linear_conversation` or `mapping`.
  * Next.js: `props.pageProps.serverResponse.data.linear_conversation`.
* **Extracted Fields**:
  * `title`: Conversation title.
  * `create_time`: Creation epoch timestamp.
  * `model`: Default or message-specific model version (e.g. `gpt-4o`, `gpt-5-6`, `o1`).
  * `messages`: User prompts and assistant responses (with system instruction placeholders and redacted plugin outputs filtered out).

---

## 2. Google Gemini (`https://share.gemini.google/<id>` & `https://gemini.google.com/share/<id>`)
* **Architecture**: Google Web Components (`BardChatUi`) with server OpenGraph metadata and client RPC (`batchexecute`).
* **Direct URL Fetch**:
  * Automatically follows short-link redirects (`share.gemini.google` ➔ `gemini.google.com`).
  * Uses social crawler user-agent negotiation to extract the exact conversation title from OpenGraph metadata tags.
* **Offline Saved HTML**:
  * When saved from an active browser session, parses rendered user query blocks (`query-text`, `user-query`) and model response blocks (`response-text`, `model-response`, `markdown`).

---

## 3. Claude (`https://claude.ai/share/<share-id>`)
* **Architecture**: Client Single-Page Application (SPA) with Cloudflare bot verification and asynchronous `/api/chat_snapshots/` endpoints.
* **Extraction Strategies**:
  * **Direct API Endpoint**: Attempts `/api/chat_snapshots/<share-id>?rendering_mode=messages&render_all_tools=true`.
  * **Hydration State**: Parses embedded `chat_messages` JSON objects.
  * **Rendered DOM**: Parses offline browser-saved HTML with `data-testid="user-message"` and `data-testid="assistant-message"` elements.

---

## 4. Perplexity (`https://www.perplexity.ai/search/<id>`)
* **Architecture**: React Single-Page Application (`<div id="root"></div>`) behind Cloudflare challenges.
* **Extraction Strategies**:
  * **Metadata**: Extracts search query titles from `<meta property="og:title">` and page `<title>`.
  * **Rendered DOM**: Parses offline browser-saved HTML searching for header/query containers and `.prose` answer blocks.

---

## 5. Offline HTML & Raw Download Workflow
* If a provider blocks direct automated fetching or requires browser rendering:
  1. Open the share link in your browser.
  2. Press `Cmd+S` / `Ctrl+S` and select **Webpage, HTML Only**.
  3. Pass the saved `.html` file to the extractor:
     ```bash
     python3 scripts/extract_chat.py path/to/saved_page.html
     ```
* To save the server's raw response directly from a URL via CLI:
  ```bash
  python3 scripts/extract_chat.py "<URL>" --save-html
  ```
