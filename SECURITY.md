# Security Policy

Thank you for helping keep **AzuDl - GC2GD** safe.

AzuDl - GC2GD is a Google Colab based downloader that can interact with Google Drive, YouTube cookies, PO Tokens, aria2 sessions, torrent metadata, and user-provided links. Because of that, users and contributors must be careful not to expose private files, account data, or credentials.

---

## Supported Versions

Security fixes are generally applied to the latest public release.

| Version | Supported |
|---|---|
| `1.3.0 GUI Beta` | Yes |
| Older versions | Best effort |

If you are using an older version, please update to the latest release before reporting a security issue.

---

## Sensitive Files

Never commit, upload, share, or publish real credentials or private session files.

Examples of sensitive files include:

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
*.torrent from private trackers
```

These files may contain private account data, authentication material, private tracker metadata, or download history.

---

## YouTube Cookies and PO Tokens

AzuDl may support YouTube cookies and PO Tokens for user-owned sessions when YouTube requires authentication.

Important rules:

- Never commit real YouTube cookies.
- Never commit real PO Tokens.
- Never paste cookies or tokens into public GitHub issues.
- Never share screenshots that reveal cookie values, tokens, account IDs, or private URLs.
- Use placeholder values when sharing examples.

Example safe placeholder:

```text
mweb+YOUR_PO_TOKEN
```

Unsafe example:

```text
mweb+real_private_token_value_here
```

---

## Google Drive Safety

AzuDl saves files to Google Drive under:

```text
/content/drive/MyDrive/AzuDl-GC2GD
```

Before sharing logs or screenshots, remove private information such as:

- Google account names
- Private folder names
- Private file names
- Private download URLs
- Personal Drive paths
- Download history entries

---

## Torrent and Private Tracker Safety

For private trackers:

- Prefer using `.torrent` files instead of magnet links.
- Do not share private `.torrent` files.
- Do not upload private tracker screenshots with passkeys, announce URLs, or tracker-specific IDs.
- Do not paste private tracker announce URLs into GitHub issues.
- Remove passkeys and private query parameters before sharing logs.

Unsafe example:

```text
https://tracker.example/announce.php?passkey=REAL_PRIVATE_PASSKEY
```

Safe example:

```text
https://tracker.example/announce.php?passkey=REDACTED
```

---

## Reporting a Vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Use one of these methods instead:

1. GitHub Security Advisories, if available for this repository.
2. Contact the maintainer privately through the official project links in the README.

When reporting a vulnerability, please include:

- A clear description of the issue
- Affected AzuDl version
- Steps to reproduce
- Impact
- Whether any credentials, cookies, tokens, or private files were exposed
- Suggested fix, if you have one

Please remove or redact all private data before sending logs or screenshots.

---

## Public Issue Guidelines

Public GitHub issues are fine for normal bugs, feature requests, and UI problems.

Do not include:

- Real cookies
- Real PO Tokens
- Google account data
- Private tracker passkeys
- Private `.torrent` files
- Private download links
- Full download history containing private data

Use placeholders instead.

---

## Responsible Disclosure

If you find a security problem, please give the maintainer reasonable time to investigate and fix it before public disclosure.

The goal is to protect users, their accounts, and their private files.
