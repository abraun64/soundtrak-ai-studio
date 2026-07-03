# Gallery quick-actions setup — one-time, ~1 minute (Windows)

Makes the gallery lightbox buttons behave natively:
- **✏️ Edit copy** → opens the `.md` in VS Code (if installed) or Notepad, instead of rendering in the browser
- **📁 Open folder** → opens the asset folder in File Explorer, instead of a browser directory listing

Without this, the buttons still work — they just fall back to the browser's default behaviour. This setup is optional polish. It **auto-detects wherever you installed the system**, so there's nothing to edit.

## Step 1 — register the protocol (once)

Open **PowerShell** in your project root (the `Marketing AI System` folder) and run:

```powershell
powershell -ExecutionPolicy Bypass -File ".\.claude\skills\asset-gallery\protocol\setup-protocol.ps1"
```

It prints `gallery-open: protocol registered.` It writes one **user-level** registry key (`HKCU\Software\Classes\gallery-open`) — no admin rights needed. It figures out its own install path, so it works no matter where you unzipped the system.

**To undo later:** run the same command with `-Remove` appended, or delete `HKEY_CURRENT_USER\Software\Classes\gallery-open` in `regedit`.

## Step 2 — first click in the browser (once per browser)

The first time you click **Edit copy** or **Open folder** in any gallery, the browser shows a dialog like *"Open gallery-open?"* / *"This site is trying to open an application"*.

- Tick **"Always allow"**
- Click **Open**

After that, both buttons work silently.

## What the handler does (and refuses)

`gallery-open.ps1` receives the path, then:
- **Folder** → `explorer.exe <folder>`
- **File** → VS Code if `code` is on PATH, else Notepad
- **Refuses any path outside your install root** (auto-detected from the handler's own location) — a malicious page can't use it to open arbitrary files.

## If nothing happens on click

1. Confirm Step 1 ran (`regedit` → `HKEY_CURRENT_USER\Software\Classes\gallery-open` exists).
2. Rebuild the gallery (`python .claude/skills/asset-gallery/build-gallery.py --campaign <slug>`) so the buttons carry the `gallery-open:` links.
3. Check the browser didn't permanently block the protocol (site settings → permissions).
