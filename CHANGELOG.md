# Changelog

All notable changes to **AzuDl - GC2GD** will be documented in this file.

This project follows a simple release history format. Versions are listed from newest to oldest.

---

## `1.3.0 GUI Beta`

### Added

- Added the first Google Colab widget-based graphical interface.
- Added default GUI launch mode.
- Added classic CLI fallback.
- Added tab-based GUI layout.
- Added Dashboard tab.
- Added Auto download tab.
- Added Direct download tab.
- Added YouTube download tab.
- Added Torrent tab.
- Added Batch download tab.
- Added Files and checksum tab.
- Added Archives tab.
- Added Maintenance tab.
- Added Developer tab.
- Added Guide tab.
- Added Google Drive storage cards.
- Added used/free storage progress display.
- Added output console inside the GUI.
- Added GUI buttons for common actions.
- Added GUI form fields for links, folders, file names, headers, speed limits, quality selection, and options.
- Added GUI controls for YouTube audio-only mode, playlist mode, and metadata saving.
- Added GUI controls for torrent private mode and seeding.
- Added GUI access to aria2 status.
- Added GUI access to save aria2 session.
- Added GUI access to clear stopped aria2 tasks.
- Added GUI access to remove aria2 GID.
- Added GUI access to download history.
- Added GUI access to latest file view.
- Added GUI access to file listing.
- Added GUI access to SHA256 tools.
- Added GUI access to ZIP folder tools.
- Added GUI access to YouTube cookie help.
- Added GUI access to YouTube PO Token help.
- Added GUI access to developer and project links.
- Added GitHub-ready user-facing text for the beta GUI release.

### Changed

- Changed the default interface from CLI-first behavior to GUI-first behavior.
- Improved public-facing help text.
- Improved GUI labels, descriptions, and button text.
- Improved layout for new users who do not want to type CLI menu numbers.
- Improved guidance around cookies, tokens, and private files.
- Updated version label to `1.3.0 GUI Beta`.

### Notes

- This is a beta GUI release.
- The classic CLI is still available with `main()`.
- CLI mode can also be forced with:

```python
import os
os.environ["AZUDL_INTERFACE"] = "cli"
```

---

## `1.2.8`

### Added

- Added torrent InfoHash detection before adding `.torrent` files.
- Added duplicate torrent detection.
- Added resume or monitor behavior for existing aria2 torrent tasks.
- Added automatic removal of existing errored torrent tasks.
- Added improved aria2 status output with InfoHash.

### Changed

- Improved torrent reliability.
- Improved duplicate torrent handling.
- Improved handling of aria2 `InfoHash is already registered` errors.

### Kept

- Kept dedicated Torrent Tools menu.
- Kept private torrent mode.
- Kept live seeding status.
- Kept aria2 session persistence.
- Kept YouTube audio format fix.
- Kept ZIP, SHA256, history, and file tools.

---

## `1.2.7`

### Fixed

- Fixed tqdm boolean evaluation error during seeding status display.

---

## `1.2.6`

### Changed

- Moved torrent features into a dedicated Torrent Tools menu.
- Improved CLI organization for torrent-related actions.

---

## `1.2.5`

### Added

- Added live torrent seeding status.
- Added upload speed display during seeding.
- Added uploaded size display during seeding.
- Added ratio display during seeding.
- Added seeding elapsed time display.
- Added aria2 session persistence.
- Added resume-friendly aria2 settings.

---

## `1.2.4`

### Fixed

- Fixed invalid infinite `seed-time=-1` issue.
- Replaced invalid infinite seed time with a long valid seed time.

### Notes

- AzuDl uses `525600` minutes as a practical long seeding time.
- Google Colab will usually disconnect long before that, so this effectively means seeding continues while the runtime is alive.

---

## `1.2.3`

### Improved

- Improved `.torrent` download validation.
- Improved aria2 RPC error messages.
- Improved handling of invalid torrent file responses.

---

## Suggested Commit Messages

For the GUI beta release:

```text
release: AzuDl GC2GD v1.3.0 GUI Beta
```

Alternative:

```text
feat(gui): add Colab widget interface beta
```

For security/documentation files:

```text
docs: add security contributing changelog and issue templates
```
