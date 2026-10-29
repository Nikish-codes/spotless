#!/bin/bash
#
# SPOTLESS - Installation Script
# Supports: Flatpak Spotify only
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$HOME/.local/share/spotless"
BIN_DIR="$HOME/.local/bin"

print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "    ░▒▓███████▓▒░▒▓███████▓▒░  ░▒▓██████▓▒░▒▓████████▓▒░▒▓█▓▒░      ░▒▓████████▓▒░░▒▓███████▓▒░▒▓███████▓▒░  "
    echo "    ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░     ░▒▓█▓▒░        "
    echo "    ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░     ░▒▓█▓▒░        "
    echo "    ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓██████▓▒░  ░▒▓██████▓▒░░▒▓██████▓▒░   "
    echo "         ░▒▓█▓▒ ░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░             ░▒▓█▓▒░     ░▒▓█▓▒░    "
    echo "         ░▒▓█▓▒ ░▒▓█▓▒░       ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░   ░▒▓█▓▒░      ░▒▓█▓▒░             ░▒▓█▓▒░     ░▒▓█▓▒░    "
    echo "   ░▒▓███████▓▒░░▒▓█▓▒░        ░▒▓██████▓▒░  ░▒▓█▓▒░   ░▒▓████████▓▒░▒▓████████▓▒░▒▓███████▓▒░▒▓███████▓▒░  "
    echo -e "${NC}"
    echo -e "${GREEN}Spotify Ad Blocker for Linux${NC}"
    echo ""
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed."
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install python3"
        echo "  Fedora: sudo dnf install python3"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log_success "Python $PYTHON_VERSION found"
}

detect_spotify() {
    log_info "Checking Spotify installation..."
    
    local found_snap=0
    local found_native=0
    local found_flatpak=0
    
    # Check Snap installation
    if command -v snap &> /dev/null && snap list spotify &> /dev/null 2>&1; then
        found_snap=1
    fi
    
    # Check Flatpak installation
    if command -v flatpak &> /dev/null && flatpak list 2>/dev/null | grep -q "com.spotify.Client"; then
        found_flatpak=1
    fi
    
    # Check native installations
    local native_paths=(
        "/usr/share/spotify"
        "/opt/spotify"
        "/usr/lib/spotify"
        "/usr/lib/spotify-client"
    )
    
    for path in "${native_paths[@]}"; do
        if [[ -d "$path" ]] && [[ -f "$path/Apps/xpui.spa" || -f "$path/xpui.spa" ]]; then
            found_native=1
            break
        fi
    done
    
    if [[ $found_snap -eq 1 || $found_native -eq 1 ]]; then
        log_error "Unsupported Spotify installation detected."
        echo ""
        echo "SPOTLESS is optimized for the Flatpak version only."
        echo "Please remove other Spotify installations:"
        echo "  Snap: sudo snap remove spotify"
        echo "  Native (.deb/.rpm): uninstall via your package manager"
        exit 1
    fi
    
    if ! command -v flatpak &> /dev/null; then
        log_error "Flatpak is required but not installed."
        echo ""
        echo "Install Flatpak first:"
        echo "  Ubuntu/Debian: sudo apt install flatpak"
        echo "  Fedora: sudo dnf install flatpak"
        exit 1
    fi
    
    if [[ $found_flatpak -ne 1 ]]; then
        log_error "Flatpak Spotify (com.spotify.Client) not found!"
        echo ""
        echo "Install Spotify Flatpak:"
        echo "  flatpak install flathub com.spotify.Client"
        exit 1
    fi
    
    log_success "Found Flatpak Spotify installation"
}

install_patcher() {
    log_info "Installing SPOTLESS..."
    
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"
    
    cp "$PROJECT_DIR/src/patcher.py" "$INSTALL_DIR/"
    mkdir -p "$PROJECT_DIR/configs"
    cp -r "$PROJECT_DIR/configs" "$INSTALL_DIR/"
    
    chmod +x "$INSTALL_DIR/patcher.py"
    
    ln -sf "$INSTALL_DIR/patcher.py" "$BIN_DIR/spotless"
    
    log_success "Installed to $INSTALL_DIR"
}

apply_patches() {
    log_info "Applying patches to Spotify..."
    
    python3 "$INSTALL_DIR/patcher.py" --verbose
}

add_to_path() {
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        log_info "Adding ~/.local/bin to PATH..."
        
        SHELL_RC=""
        if [[ -n "$ZSH_VERSION" ]] || [[ "$SHELL" == *"zsh"* ]]; then
            SHELL_RC="$HOME/.zshrc"
        elif [[ -n "$BASH_VERSION" ]] || [[ "$SHELL" == *"bash"* ]]; then
            SHELL_RC="$HOME/.bashrc"
        fi
        
        if [[ -n "$SHELL_RC" ]] && [[ -f "$SHELL_RC" ]]; then
            if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$SHELL_RC"; then
                echo '' >> "$SHELL_RC"
                echo '# Added by SPOTLESS' >> "$SHELL_RC"
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
                log_info "Added PATH to $SHELL_RC"
                log_warning "Run 'source $SHELL_RC' or restart your terminal"
            fi
        fi
    fi
}

print_completion() {
    echo ""
    echo -e "${GREEN}${BOLD}Installation Complete!${NC}"
    echo ""
    echo "Usage:"
    echo "  spotless          - Run the patcher"
    echo "  spotless --status - Check patch status"
    echo "  spotless --restore - Restore original Spotify"
    echo ""
    echo "Note: After Spotify updates, run 'spotless' again to reapply patches."
    if ! command -v spotless &> /dev/null; then
        echo ""
        echo "If 'spotless' isn't found, run:"
        echo "  export PATH=\"$HOME/.local/bin:\$PATH\""
        echo "  hash -r"
    fi
    echo ""
}

main() {
    print_banner
    log_warning "Warning: SPOTLESS is optimized for Flatpak Spotify (com.spotify.Client)."
    check_dependencies
    detect_spotify
    install_patcher
    apply_patches
    add_to_path
    print_completion
}

main "$@"
