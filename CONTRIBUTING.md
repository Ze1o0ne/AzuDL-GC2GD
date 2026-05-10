# Contributing to AzuDl - GC2GD

Thank you for your interest in contributing to **AzuDl - GC2GD**.

AzuDl - GC2GD is a Google Colab based universal downloader that saves supported downloads directly to Google Drive. It supports direct links, YouTube videos and playlists, torrent magnet links, `.torrent` files, private torrent mode, batch downloads, history, ZIP tools, SHA256 tools, aria2 status monitoring, seeding status, duplicate torrent detection, and a Colab GUI beta.

Contributions are welcome, especially bug fixes, documentation improvements, UI improvements, Colab compatibility fixes, and safer user experience improvements.

---

## Before You Start

Please read:

- `README.md`
- `README.fa.md`, if you read Persian
- `SECURITY.md`
- `CHANGELOG.md`

Make sure your change matches the purpose of the project.

---

## Ways to Contribute

You can help by:

- Reporting bugs
- Improving the GUI
- Improving README or Persian documentation
- Improving help text
- Fixing Colab compatibility issues
- Improving YouTube download handling
- Improving torrent handling
- Improving aria2 session handling
- Improving error messages
- Adding safer defaults
- Adding screenshots or examples
- Testing on Google Colab

---

## Security First

Do **not** commit sensitive files.

Never commit:

```text
cookies.txt
youtube_cookies.txt
*_cookies.txt
*.cookies
youtube_po_token.txt
youtube_visitor_data.txt
aria2_rpc_secret.txt
aria2.session
download_history.json
private .torrent files
```

Do not include real tokens, cookies, passkeys, private tracker URLs, or private Google Drive paths in issues, pull requests, screenshots, logs, examples, or tests.

Use placeholders instead:

```text
YOUR_COOKIE_FILE
YOUR_PO_TOKEN
REDACTED
example.com
```

---

## Development Environment

AzuDl is designed primarily for Google Colab.

Required Python packages:

```text
requests
tqdm
yt-dlp
ipywidgets
```

Required system tools in Colab:

```text
aria2
ffmpeg
p7zip-full
```

The script installs or checks these tools automatically inside Colab.

---

## Running the Project

### GUI mode

The default interface in `1.3.0 GUI Beta` is the GUI.

```python
launch_gui()
```

### CLI mode

The classic CLI is still available:

```python
main()
```

You can force CLI mode with:

```python
import os
os.environ["AZUDL_INTERFACE"] = "cli"
```

---

## Testing Before Pull Request

Before opening a pull request, test the affected area in Google Colab.

Recommended basic checks:

1. Run the notebook or script in a fresh Colab runtime.
2. Confirm Google Drive mount works.
3. Confirm GUI launches.
4. Confirm CLI can still be launched manually.
5. Confirm storage report works.
6. Confirm download history does not crash.
7. Confirm file listing does not crash.
8. Confirm aria2 RPC starts successfully.
9. Confirm help text displays correctly.
10. Confirm no private files are created inside the repository.

If you changed a specific feature, test that feature directly.

Examples:

| Change Type | Suggested Test |
|---|---|
| GUI layout | Launch GUI and check all tabs |
| Direct download | Test a small public direct file |
| YouTube | Test a public short video |
| Torrent | Test only legal public torrents |
| Batch | Test mixed public links |
| ZIP tools | ZIP a small test folder |
| SHA256 | Hash a small test file |
| Docs | Check Markdown rendering on GitHub |

---

## Pull Request Guidelines

Please keep pull requests focused.

Good examples:

- Fix one bug
- Improve one GUI tab
- Add one documentation section
- Improve one error message group
- Update one release note

Avoid very large pull requests that mix unrelated changes.

---

## Code Style

Please keep the code simple and readable.

Guidelines:

- Use clear function and variable names.
- Keep user-facing text professional and easy to understand.
- Avoid hardcoded private paths.
- Avoid real tokens, cookies, and secrets.
- Keep Colab compatibility in mind.
- Prefer safe defaults.
- Preserve CLI compatibility when changing GUI logic.
- Preserve GUI compatibility when changing core download logic.

---

## User-Facing Text Style

This project is used by public GitHub users, including non-expert users.

Good user-facing text should be:

- Clear
- Short
- Helpful
- Safe
- Actionable

Avoid:

- Internal-only wording
- Unclear abbreviations
- Aggressive wording
- Overly technical text without explanation
- Instructions that encourage unsafe sharing of credentials

---

## Documentation Guidelines

When updating documentation:

- Keep English README and Persian README aligned when possible.
- Use placeholders for private values.
- Mention Colab limitations clearly.
- Mention that cookies and PO Tokens must stay private.
- Mention that permanent torrent seeding should use a VPS or seedbox.
- Keep changelog entries clear and versioned.

---

## Issue Reports

When reporting a bug, please include:

- AzuDl version
- Interface: GUI or CLI
- Google Colab runtime type
- Download type: Direct, YouTube, Torrent, Batch, Files, Archives, Maintenance
- What you expected
- What happened
- Error message
- Screenshot, if useful
- Steps to reproduce

Do not include private URLs, cookies, tokens, passkeys, or private files.

---

## Feature Requests

Good feature requests explain:

- What problem the feature solves
- Who needs it
- How it should work
- Whether it affects GUI, CLI, or both
- Any safety concerns

---

## Commit Message Suggestions

Use simple commit messages.

Examples:

```text
fix(torrent): handle duplicate infohash
feat(gui): add developer tab
docs: update gui beta readme
security: add sensitive file guidance
chore: update changelog
```

---

## License

By contributing to this project, you agree that your contribution will be released under the same license as the repository.
