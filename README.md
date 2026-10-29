# SPOTLESS

Spotify ad‑blocking patcher for Linux focused on blocking **audio**, **video**, and **banner** ads (plus premium prompts) in the Flatpak client.

SPOTLESS installs a small CLI (`spotless`) that patches Spotify’s `xpui.spa` bundle, creates a backup, and can restore the original files.

## Quick Demo

```bash
spotless --status
```

Example output (abridged):

```
Spotify Status:
  Installed: True
  Type: flatpak
  Path: /var/lib/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify
  Version: Unknown
  Patched: False
  Backup exists: True
```

## Key Features

- Blocks audio/video ad logic and banner placements
- Hides the top‑bar “Explore Premium” button
- Disables telemetry (Sentry)
- Safe backup + restore
- Dry‑run and status modes

## Project Layout

```
spotless/
├── src/
│   └── patcher.py        # Main CLI patcher (installed as `spotless`)
├── configs/              # Configuration templates
├── scripts/
│   ├── install.sh        # Installs CLI and applies patches
│   └── uninstall.sh      # Restores and removes installed files
└── LICENSE
```

## Getting Started

### Prerequisites

- Python 3.8+
- Flatpak
- Spotify Flatpak (`com.spotify.Client`)
- `sudo` (needed for system Flatpak installs under `/var/lib/flatpak`)

### Install Spotify (Flatpak)

Ubuntu/Debian:

```bash
sudo apt install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub com.spotify.Client
```

Fedora:

```bash
sudo dnf install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install flathub com.spotify.Client
```

### Install SPOTLESS

```bash
git clone https://github.com/Nikish-codes/spotless.git
cd spotless
./scripts/install.sh
```

If `spotless` isn’t found:

```bash
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

### Launch Spotify

```bash
flatpak run com.spotify.Client
```

## Usage

Apply patches:

```bash
spotless
```

Show status:

```bash
spotless --status
```

Dry‑run (no changes):

```bash
spotless --dry-run --verbose
```

Restore from backup:

```bash
spotless --restore
```

Advanced flags:

```bash
spotless --path /var/lib/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify
spotless --config /path/to/config.json
spotless --verbose
```

## Configuration

`spotless` accepts an optional JSON config file via `--config`. Only `custom_patches` is currently used.

Example `config.json`:

```json
{
  "custom_patches": [
    {
      "name": "example_patch",
      "file": "*.js",
      "signature": "original_string",
      "replacement": "new_string",
      "is_regex": false
    }
  ]
}
```


## How It Works

1. Detects the Flatpak Spotify path (system or user)
2. Creates `xpui.spa.bak` if it does not already exist
3. Extracts `xpui.spa` (a ZIP archive) to a temp directory
4. Applies built‑in string and regex patches to JS/CSS assets
5. Rebuilds and replaces the patched `xpui.spa`

If the install path is not writable, the patcher escalates using `sudo` for file copy and permission changes.

## Uninstall / Removal

```bash
./scripts/uninstall.sh
```

This restores the original Spotify files (if a backup exists) and removes:

- `~/.local/share/spotless`
- `~/.local/bin/spotless`

## Testing and Quality

There is no automated test suite yet. For a quick validation:

```bash
spotless --dry-run --verbose
spotless --status
```

## Troubleshooting

1) `spotless: command not found`
- Add `~/.local/bin` to PATH (see install section).

2) "Unsupported Spotify installation detected"
- Remove Snap/native Spotify packages and keep only Flatpak.

3) "Flatpak Spotify not found"
- Install `com.spotify.Client` from Flathub.

4) "Need elevated privileges"
- System Flatpak installs live under `/var/lib/flatpak`.

5) "0 patches applied"
- Spotify may have changed signatures. Update `src/patcher.py` and re‑run.

6) "xpui.spa not found"
- Reinstall the Flatpak client or run `flatpak repair --user`.

## Contributing

Contributions are welcome. Keep changes focused and easy to review.

1) Fork the repo and create a feature branch
2) Make minimal, clear changes
3) Run `spotless --dry-run --verbose` to sanity‑check
4) Open a PR with a short summary and any relevant logs

## License

GPL-3.0-only. See `LICENSE`.
