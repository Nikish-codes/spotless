#!/bin/bash
#
# SPOTLESS - Uninstallation Script
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="$HOME/.local/share/spotless"
BIN_DIR="$HOME/.local/bin"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo ""
echo -e "${YELLOW}SPOTLESS - Uninstaller${NC}"
echo ""

# Restore Spotify if patched
if [[ -f "$INSTALL_DIR/patcher.py" ]]; then
    log_info "Restoring original Spotify..."
    python3 "$INSTALL_DIR/patcher.py" --restore 2>/dev/null || true
fi

# Remove installed files
log_info "Removing installed files..."

rm -f "$BIN_DIR/spotless"
rm -f "$BIN_DIR/spotify-spotless"
rm -rf "$INSTALL_DIR"

log_success "SPOTLESS has been uninstalled."
echo ""
echo "Note: Spotify has been restored to its original state."
echo "If you experience issues, reinstall Spotify:"
echo "  Flatpak: flatpak update com.spotify.Client"
echo ""
