# Contributing to Shared Chat Extractor

Thank you for your interest in contributing! 🎉

## How to Contribute

### Reporting Bugs

1. Check if the issue already exists in [Issues](../../issues).
2. Create a new issue using the [bug report template](.github/ISSUE_TEMPLATE.md).
3. Include the platform (ChatGPT, Claude, etc.), the error message, and steps to reproduce.

### Adding Support for a New Platform

1. Identify the platform's share URL pattern and data format.
2. Create a new parser function in `scripts/extract_chat.py` following the existing pattern:
   ```python
   def parse_new_platform(html: str, next_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
       """Parse NewPlatform share page."""
       # Your parsing logic here
       return {
           "platform": "NewPlatform",
           "title": title,
           "messages": messages
       }
   ```
3. Add the parser to the detection chain in `main()`.
4. Document the payload format in `references/providers.md`.
5. Add example outputs in `examples/`.

### Code Style

- Use Python 3.7+ compatible syntax.
- Keep **zero external dependencies** (standard library only).
- Add type hints to function signatures.
- Include docstrings for all public functions.

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Gemini share link support
fix: handle empty message parts in Claude parser
docs: add example for JSON output format
```

### Pull Request Process

1. Fork the repo and create a feature branch.
2. Make your changes with tests if applicable.
3. Update `references/providers.md` if adding a new platform.
4. Submit a PR with a clear description of the change.

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to make this tool better for everyone.
