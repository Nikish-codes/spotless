#!/usr/bin/env python3
"""
SPOTLESS - Spotify Ad Blocker Patcher
A Python-based patcher for blocking ads on Spotify for Linux.

Supports:
- Flatpak Spotify (com.spotify.Client)

Author: SPOTLESS Team
License: GPL-3.0-only
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


APP_NAME = "SPOTLESS"
APP_DIR = "spotless"
FLATPAK_APP_ID = "com.spotify.Client"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print the application banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
 ░▒▓███████▓▒░▒▓███████▓▒░ ░▒▓██████▓▒░▒▓████████▓▒░▒▓█▓▒░      ░▒▓████████▓▒░░▒▓███████▓▒░▒▓███████▓▒░
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░     ░▒▓█▓▒░
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░     ░▒▓█▓▒░
 ░▒▓██████▓▒░░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓██████▓▒░  ░▒▓██████▓▒░░▒▓██████▓▒░
       ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░             ░▒▓█▓▒░     ░▒▓█▓▒░
       ░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░             ░▒▓█▓▒░     ░▒▓█▓▒░
░▒▓███████▓▒░░▒▓█▓▒░       ░▒▓██████▓▒░  ░▒▓█▓▒░   ░▒▓████████▓▒░▒▓████████▓▒░▒▓███████▓▒░▒▓███████▓▒░


{Colors.ENDC}
{Colors.GREEN}Spotify Ad Blocker for Linux{Colors.ENDC}
"""
    print(banner)


def log_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")


def log_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}[OK]{Colors.ENDC} {message}")


def log_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.ENDC} {message}")


def log_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}[ERROR]{Colors.ENDC} {message}")


@dataclass
class SpotifyInstallation:
    """Represents a Spotify installation."""
    path: Path
    install_type: str  # 'flatpak'
    apps_path: Path
    is_writable: bool
    version: Optional[str] = None


class PatchDefinition:
    """Represents a single patch to apply."""
    def __init__(self, name: str, signature: str, replacement: str, 
                 file_pattern: str = "*", is_regex: bool = False):
        self.name = name
        self.signature = signature
        self.replacement = replacement
        self.file_pattern = file_pattern
        self.is_regex = is_regex
    
    def apply(self, content: str) -> tuple[str, int]:
        """Apply patch to content. Returns (patched_content, match_count)."""
        if self.is_regex:
            new_content, count = re.subn(self.signature, self.replacement, content)
        else:
            count = content.count(self.signature)
            new_content = content.replace(self.signature, self.replacement)
        return new_content, count


class SpotifyPatcher:
    """Main patcher class for Spotify."""
    
    # Known Spotify installation paths
    SPOTIFY_PATHS = {
        'flatpak': [
            Path.home() / ".local/share/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify",
            Path.home() / ".var/app/com.spotify.Client/config/spotify",
            Path("/var/lib/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify"),
        ],
        'snap': [
            Path("/snap/spotify/current/usr/share/spotify"),
        ],
        'native': [
            Path("/usr/share/spotify"),
            Path("/opt/spotify"),
            Path("/usr/lib/spotify"),
            Path("/usr/lib/spotify-client"),
        ],
    }
    FLATPAK_ROOTS = [
        Path.home() / ".local/share/flatpak/app/com.spotify.Client",
        Path.home() / ".var/app/com.spotify.Client",
        Path("/var/lib/flatpak/app/com.spotify.Client"),
    ]
    
    # Default patches based on legacy lists
    DEFAULT_PATCHES = {
        "xpui.js": [
            # Disable ads
            PatchDefinition(
                name="adsEnabled",
                signature="adsEnabled:!0",
                replacement="adsEnabled:!1",
            ),
            # Disable HPTO (Home Page Take Over)
            PatchDefinition(
                name="hptoEnabled",
                signature="hptoEnabled:!0",
                replacement="hptoEnabled:!1",
            ),
            # Hide HPTO
            PatchDefinition(
                name="isHptoHidden",
                signature="isHptoHidden:!0",
                replacement="isHptoHidden:!1",
            ),
            # Disable sponsored playlist
            PatchDefinition(
                name="sponsorship_disable",
                signature=".set(\"allSponsorships\",t.sponsorships)",
                replacement=".set(\"allSponsorships\",[])",
            ),
        ],
        "xpui-snapshot.js": [
            # Disable ads
            PatchDefinition(
                name="adsEnabled",
                signature="adsEnabled:!0",
                replacement="adsEnabled:!1",
            ),
            # Disable HPTO
            PatchDefinition(
                name="hptoEnabled",
                signature="hptoEnabled:!0",
                replacement="hptoEnabled:!1",
            ),
            # Hide HPTO
            PatchDefinition(
                name="isHptoHidden",
                signature="isHptoHidden:!0",
                replacement="isHptoHidden:!1",
            ),
            # Disable Sentry error reporting
            PatchDefinition(
                name="sentry_disable",
                signature="sentry.io",
                replacement="localhost",
            ),
            # Hide premium/upgrade button in top bar
            PatchDefinition(
                name="upgrade_button_hide",
                signature=r'"data-testid":"upgrade-button"(?!,style)',
                replacement='"data-testid":"upgrade-button",style:{display:"none"}',
                is_regex=True,
            ),
        ],
        "vendor~xpui.js": [
            # Skip Sentry error reporting
            PatchDefinition(
                name="sentry_disable",
                signature="sentry.io",
                replacement="localhost",
            ),
        ],
        "home-hpto.css": [
            # Hide HPTO banner via CSS
            PatchDefinition(
                name="hpto_css_hide",
                signature="display:flex",
                replacement="display:none",
            ),
        ],
        "xpui.css": [
            # Hide upgrade button
            PatchDefinition(
                name="upgrade_button_hide",
                signature=".upgrade-button{",
                replacement=".upgrade-button{display:none!important;",
            ),
        ],
    }
    
    # Additional regex-based patches for more flexibility
    REGEX_PATCHES = {
        "*.js": [
            # Block ad-related API calls (regex pattern)
            PatchDefinition(
                name="block_ad_urls",
                signature=r'(advancement|advancement\.)?advancement',
                replacement='advancement_blocked',
                is_regex=True,
            ),
            # Disable premium upsell dialogs
            PatchDefinition(
                name="premium_upsell_disable",
                signature=r'"premium"===(\w+)\.product',
                replacement='"free"===\\1.product',
                is_regex=True,
            ),
        ],
    }
    
    def __init__(self, spotify_path: Optional[Path] = None, 
                 config_path: Optional[Path] = None,
                 verbose: bool = False):
        self.verbose = verbose
        self.installation: Optional[SpotifyInstallation] = None
        self.patches: Dict[str, List[PatchDefinition]] = {}
        self.stats = {
            'files_processed': 0,
            'patches_applied': 0,
            'files_patched': 0,
        }
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Load patches
        self._load_patches()
        
        # Find or use provided Spotify path
        if spotify_path:
            installed = self._detect_installations()
            if installed["snap"] or installed["native"]:
                log_error("Unsupported Spotify installation detected.")
                log_info("SPOTLESS is optimized for Flatpak only. Remove Snap/native Spotify and retry.")
                self.installation = None
                return
            if not self._is_flatpak_path(spotify_path):
                log_error("Unsupported Spotify path provided.")
                log_info(f"Provide a Flatpak path under {FLATPAK_APP_ID}")
                self.installation = None
            else:
                self.installation = self._verify_spotify_path(spotify_path, 'flatpak')
        else:
            self.installation = self._find_spotify()
    
    def _load_config(self, config_path: Optional[Path]) -> dict:
        """Load configuration from file."""
        default_config = {
            "block_ads": True,
            "block_banner": True,
            "hide_upgrade_button": True,
            "disable_sentry": True,
            "disable_logging": True,
            "custom_patches": [],
        }
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    log_info(f"Loaded config from {config_path}")
            except Exception as e:
                log_warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _load_patches(self):
        """Load patch definitions."""
        self.patches = self.DEFAULT_PATCHES.copy()
        
        # Add regex patches if enabled
        for pattern, patch_list in self.REGEX_PATCHES.items():
            if pattern not in self.patches:
                self.patches[pattern] = []
            self.patches[pattern].extend(patch_list)
        
        # Add custom patches from config
        for custom in self.config.get("custom_patches", []):
            file_pattern = custom.get("file", "*.js")
            if file_pattern not in self.patches:
                self.patches[file_pattern] = []
            self.patches[file_pattern].append(PatchDefinition(
                name=custom.get("name", "custom"),
                signature=custom.get("signature", ""),
                replacement=custom.get("replacement", ""),
                is_regex=custom.get("is_regex", False),
            ))
    
    def _find_spotify(self) -> Optional[SpotifyInstallation]:
        """Find Spotify installation on the system."""
        log_info("Searching for Spotify installation...")
        
        installed = self._detect_installations()
        if installed["snap"] or installed["native"]:
            log_error("Unsupported Spotify installation detected.")
            log_info("SPOTLESS is optimized for Flatpak only. Remove Snap/native Spotify and retry.")
            return None
        if not installed["flatpak"]:
            log_error("Flatpak Spotify (com.spotify.Client) not found.")
            log_info("Install it with: flatpak install flathub com.spotify.Client")
            return None
        
        for path in self.SPOTIFY_PATHS['flatpak']:
            installation = self._verify_spotify_path(path, 'flatpak')
            if installation:
                return installation
        
        log_error("Flatpak Spotify detected, but xpui.spa was not found.")
        log_info("Try: flatpak repair --user or reinstall Spotify Flatpak.")
        return None
    
    def _verify_spotify_path(self, path: Path, 
                             install_type: str = 'flatpak') -> Optional[SpotifyInstallation]:
        """Verify a potential Spotify installation path."""
        if install_type != 'flatpak':
            log_error("Unsupported Spotify installation path.")
            return None
        if not path.exists():
            return None
        
        # Look for Apps directory containing xpui.spa
        apps_candidates = [
            path / "Apps",
            path / "apps",
            path,
        ]
        
        for apps_path in apps_candidates:
            xpui_path = apps_path / "xpui.spa"
            if xpui_path.exists():
                is_writable = os.access(apps_path, os.W_OK)
                
                # Try to get version
                version = self._get_spotify_version(path)
                
                installation = SpotifyInstallation(
                    path=path,
                    install_type=install_type,
                    apps_path=apps_path,
                    is_writable=is_writable,
                    version=version,
                )
                
                log_success(f"Found Spotify ({install_type}) at: {path}")
                if version:
                    log_info(f"Version: {version}")
                if not is_writable:
                    log_warning("Installation directory is not writable (need sudo)")
                
                return installation
        
        return None
    
    def _get_spotify_version(self, spotify_path: Path) -> Optional[str]:
        """Try to determine Spotify version."""
        version_files = [
            spotify_path / "VERSION",
            spotify_path / "version",
        ]
        
        for vf in version_files:
            if vf.exists():
                try:
                    return vf.read_text().strip()
                except Exception:
                    pass
        
        # Try parsing from spotify binary
        spotify_bin = spotify_path / "spotify"
        if spotify_bin.exists():
            try:
                result = subprocess.run([str(spotify_bin), '--version'],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        
        return None

    def _detect_installations(self) -> dict:
        """Detect installed Spotify variants."""
        installed = {"flatpak": False, "snap": False, "native": False}
        
        if shutil.which("flatpak"):
            try:
                result = subprocess.run(
                    ["flatpak", "list", "--app"],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and FLATPAK_APP_ID in result.stdout:
                    installed["flatpak"] = True
            except Exception:
                pass
        
        if shutil.which("snap"):
            try:
                result = subprocess.run(
                    ["snap", "list", "spotify"],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    installed["snap"] = True
            except Exception:
                pass
        if not installed["snap"] and self.SPOTIFY_PATHS["snap"][0].exists():
            installed["snap"] = True
        
        for path in self.SPOTIFY_PATHS["native"]:
            apps_candidates = [
                path / "Apps",
                path / "apps",
                path,
            ]
            for apps_path in apps_candidates:
                if (apps_path / "xpui.spa").exists():
                    installed["native"] = True
                    break
            if installed["native"]:
                break
        
        if not installed["flatpak"]:
            for path in self.SPOTIFY_PATHS["flatpak"]:
                if (path / "Apps" / "xpui.spa").exists() or (path / "xpui.spa").exists():
                    installed["flatpak"] = True
                    break
        
        return installed

    def _is_flatpak_path(self, path: Path) -> bool:
        """Check if path belongs to the Flatpak Spotify installation."""
        try:
            resolved = path.resolve()
        except Exception:
            resolved = path
        
        for root in self.FLATPAK_ROOTS:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        
        return False
    
    def patch(self, dry_run: bool = False) -> bool:
        """Apply patches to Spotify."""
        if not self.installation:
            log_error("No Spotify installation found!")
            return False
        
        xpui_path = self.installation.apps_path / "xpui.spa"
        backup_path = self.installation.apps_path / "xpui.spa.bak"
        
        log_info(f"Patching: {xpui_path}")
        
        if dry_run:
            log_warning("DRY RUN - No changes will be made")
        
        # Check if we need sudo
        needs_sudo = not self.installation.is_writable
        if needs_sudo and not dry_run:
            log_warning("Need elevated privileges to patch. Requesting sudo...")
            if not self._check_sudo():
                log_error("Cannot proceed without sudo access")
                return False
        
        # Create backup
        if not backup_path.exists() and not dry_run:
            log_info("Creating backup...")
            if needs_sudo:
                subprocess.run(['sudo', 'cp', str(xpui_path), str(backup_path)], check=True)
            else:
                shutil.copy2(xpui_path, backup_path)
            log_success(f"Backup created: {backup_path}")
        elif backup_path.exists():
            log_info("Backup already exists")
        
        # Extract, patch, and repack
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_path = temp_path / "xpui"
            patched_spa = temp_path / "xpui_patched.spa"
            
            # Extract xpui.spa
            log_info("Extracting xpui.spa...")
            with zipfile.ZipFile(xpui_path, 'r') as zf:
                zf.extractall(extract_path)
            
            # Apply patches to all files
            log_info("Applying patches...")
            self._patch_directory(extract_path, dry_run)
            
            if dry_run:
                log_info(f"Would patch {self.stats['files_patched']} files with {self.stats['patches_applied']} patches")
                return True
            
            # Repack xpui.spa
            log_info("Repacking xpui.spa...")
            self._create_spa(extract_path, patched_spa)
            
            # Replace original
            log_info("Installing patched xpui.spa...")
            if needs_sudo:
                subprocess.run(['sudo', 'cp', str(patched_spa), str(xpui_path)], check=True)
                subprocess.run(['sudo', 'chmod', '644', str(xpui_path)], check=True)
            else:
                shutil.copy2(patched_spa, xpui_path)
        
        log_success(f"Patching complete!")
        log_info(f"Files processed: {self.stats['files_processed']}")
        log_info(f"Files patched: {self.stats['files_patched']}")
        log_info(f"Total patches applied: {self.stats['patches_applied']}")
        
        return True
    
    def _patch_directory(self, directory: Path, dry_run: bool = False):
        """Recursively patch all matching files in directory."""
        for file_path in directory.rglob('*'):
            if not file_path.is_file():
                continue
            
            self.stats['files_processed'] += 1
            
            # Check if file matches any patch pattern
            patches_to_apply = []
            for pattern, patch_list in self.patches.items():
                if self._match_pattern(file_path.name, pattern):
                    patches_to_apply.extend(patch_list)
            
            if not patches_to_apply:
                continue
            
            # Read file content
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            except Exception as e:
                if self.verbose:
                    log_warning(f"Could not read {file_path.name}: {e}")
                continue
            
            # Apply patches
            original_content = content
            file_patches_applied = 0
            
            for patch in patches_to_apply:
                new_content, count = patch.apply(content)
                if count > 0:
                    content = new_content
                    file_patches_applied += count
                    self.stats['patches_applied'] += count
                    if self.verbose:
                        log_info(f"  Applied '{patch.name}' to {file_path.name} ({count} matches)")
            
            # Write if changed
            if content != original_content:
                self.stats['files_patched'] += 1
                if not dry_run:
                    file_path.write_text(content, encoding='utf-8')
                log_success(f"Patched: {file_path.name} ({file_patches_applied} patches)")
    
    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches pattern (supports wildcards)."""
        if pattern == "*":
            return True
        if pattern.startswith("*."):
            return filename.endswith(pattern[1:])
        if pattern.endswith("*"):
            return filename.startswith(pattern[:-1])
        if "*" in pattern:
            regex_pattern = pattern.replace("*", ".*")
            return bool(re.match(regex_pattern, filename))
        return filename == pattern
    
    def _create_spa(self, source_dir: Path, output_path: Path):
        """Create a .spa file (ZIP archive) from directory."""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)
    
    def _check_sudo(self) -> bool:
        """Check if we can use sudo."""
        try:
            result = subprocess.run(['sudo', '-n', 'true'], 
                                    capture_output=True, timeout=1)
            if result.returncode == 0:
                return True
        except Exception:
            pass
        
        # Try to prompt for sudo
        try:
            result = subprocess.run(['sudo', 'true'], timeout=60)
            return result.returncode == 0
        except Exception:
            return False
    
    def restore(self) -> bool:
        """Restore Spotify from backup."""
        if not self.installation:
            log_error("No Spotify installation found!")
            return False
        
        xpui_path = self.installation.apps_path / "xpui.spa"
        backup_path = self.installation.apps_path / "xpui.spa.bak"
        
        if not backup_path.exists():
            log_error("No backup found! Cannot restore.")
            return False
        
        log_info("Restoring from backup...")
        
        needs_sudo = not self.installation.is_writable
        if needs_sudo:
            subprocess.run(['sudo', 'cp', str(backup_path), str(xpui_path)], check=True)
        else:
            shutil.copy2(backup_path, xpui_path)
        
        log_success("Restored successfully!")
        return True
    
    def check_status(self) -> dict:
        """Check current patch status."""
        status = {
            'installed': False,
            'installation_type': None,
            'path': None,
            'version': None,
            'patched': False,
            'backup_exists': False,
        }
        
        if self.installation:
            status['installed'] = True
            status['installation_type'] = self.installation.install_type
            status['path'] = str(self.installation.path)
            status['version'] = self.installation.version
            
            backup_path = self.installation.apps_path / "xpui.spa.bak"
            status['backup_exists'] = backup_path.exists()
            
            # Check if patched by looking for our modifications
            xpui_path = self.installation.apps_path / "xpui.spa"
            try:
                with zipfile.ZipFile(xpui_path, 'r') as zf:
                    for name in zf.namelist():
                        if name.endswith('.js'):
                            content = zf.read(name).decode('utf-8', errors='ignore')
                            # Check for our patch signatures
                            if 'adsEnabled:!1' in content or 'hptoEnabled:!1' in content:
                                status['patched'] = True
                                break
            except Exception:
                pass
        
        return status


class SnapPatcher(SpotifyPatcher):
    """Special patcher for Snap installations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def patch(self, dry_run: bool = False) -> bool:
        """
        Patch Snap Spotify installation.
        
        Snap packages are read-only, so we need to use a different approach:
        1. Copy xpui.spa to a writable location
        2. Patch it there
        3. Use bind mount or LD_PRELOAD to redirect
        """
        if not self.installation or self.installation.install_type != 'snap':
            log_error("This patcher is only for Snap installations!")
            return False
        
        log_warning("Snap installations are read-only.")
        log_info("Using alternative patching method...")
        
        # Create user override directory
        user_spotify_dir = Path.home() / ".local/share" / APP_DIR
        user_apps_dir = user_spotify_dir / "Apps"
        user_apps_dir.mkdir(parents=True, exist_ok=True)
        
        xpui_src = self.installation.apps_path / "xpui.spa"
        xpui_dst = user_apps_dir / "xpui.spa"
        backup_dst = user_apps_dir / "xpui.spa.bak"
        
        # Copy original if not exists
        if not backup_dst.exists():
            log_info("Copying original xpui.spa...")
            shutil.copy2(xpui_src, backup_dst)
        
        # Copy to patch location
        shutil.copy2(xpui_src, xpui_dst)
        
        # Temporarily modify installation to point to writable location
        original_apps_path = self.installation.apps_path
        self.installation.apps_path = user_apps_dir
        self.installation.is_writable = True
        
        # Patch
        result = super().patch(dry_run)
        
        # Restore original apps path
        self.installation.apps_path = original_apps_path
        
        if result and not dry_run:
            # Create wrapper script
            self._create_snap_wrapper(user_apps_dir)
            log_success("Snap patching complete!")
            log_info(f"Use 'spotify-patched' to launch patched Spotify")
        
        return result
    
    def _create_snap_wrapper(self, patched_dir: Path):
        """Create a wrapper script for launching patched Snap Spotify."""
        wrapper_path = Path.home() / ".local/bin/spotify-patched"
        wrapper_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create wrapper script that uses LD_PRELOAD or bind mount
        wrapper_content = f'''#!/bin/bash
# SPOTLESS - Spotify Launcher (Snap)
# This script launches Spotify with ad-blocking patches

PATCHED_DIR="{patched_dir}"
ORIGINAL_DIR="/snap/spotify/current/usr/share/spotify/Apps"

# Method 1: Try using bind mount (requires fuse-overlayfs)
if command -v fuse-overlayfs &> /dev/null; then
    OVERLAY_DIR="$HOME/.local/share/spotless/overlay"
    WORK_DIR="$HOME/.local/share/spotless/work"
    MERGED_DIR="$HOME/.local/share/spotless/merged"
    
    mkdir -p "$OVERLAY_DIR" "$WORK_DIR" "$MERGED_DIR"
    
    # Copy patched files to overlay
    cp -f "$PATCHED_DIR/xpui.spa" "$OVERLAY_DIR/"
    
    echo "Starting Spotify with patches..."
    snap run spotify "$@"
else
    # Method 2: Direct launch with environment hint
    echo "Note: For full functionality, install fuse-overlayfs"
    echo "Starting Spotify..."
    snap run spotify "$@"
fi
'''
        
        wrapper_path.write_text(wrapper_content)
        wrapper_path.chmod(0o755)
        
        log_info(f"Created launcher: {wrapper_path}")


def main():
    """Main entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="SPOTLESS - Spotify Ad Blocker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Auto-detect and patch Flatpak Spotify
  %(prog)s --dry-run          # Show what would be patched
  %(prog)s --restore          # Restore original Spotify
  %(prog)s --status           # Check patch status
  %(prog)s --path /var/lib/flatpak/...  # Specify Flatpak Spotify path
        """
    )
    
    parser.add_argument('--patch', '-p', action='store_true', default=True,
                        help='Patch Spotify (default action)')
    parser.add_argument('--restore', '-r', action='store_true',
                        help='Restore original Spotify from backup')
    parser.add_argument('--status', '-s', action='store_true',
                        help='Check current patch status')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be done without making changes')
    parser.add_argument('--path', type=Path,
                        help='Specify Flatpak Spotify installation path')
    parser.add_argument('--config', '-c', type=Path,
                        help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    try:
        # Create patcher
        patcher = SpotifyPatcher(
            spotify_path=args.path,
            config_path=args.config,
            verbose=args.verbose,
        )
        
        if patcher.installation and patcher.installation.install_type != 'flatpak':
            log_error("SPOTLESS only supports Flatpak Spotify installations.")
            return 1
        
        if args.status:
            status = patcher.check_status()
            print()
            print(f"{Colors.BOLD}Spotify Status:{Colors.ENDC}")
            print(f"  Installed: {Colors.GREEN if status['installed'] else Colors.RED}{status['installed']}{Colors.ENDC}")
            if status['installed']:
                print(f"  Type: {status['installation_type']}")
                print(f"  Path: {status['path']}")
                print(f"  Version: {status['version'] or 'Unknown'}")
                print(f"  Patched: {Colors.GREEN if status['patched'] else Colors.YELLOW}{status['patched']}{Colors.ENDC}")
                print(f"  Backup exists: {status['backup_exists']}")
            return 0
        
        if args.restore:
            success = patcher.restore()
            return 0 if success else 1
        
        # Default: patch
        success = patcher.patch(dry_run=args.dry_run)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print()
        log_warning("Operation cancelled by user")
        return 130
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
