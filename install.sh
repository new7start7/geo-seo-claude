#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# GEO-SEO Codex Skill Installer
# Installs the GEO-first SEO analysis tool for Codex
# ============================================================

REPO_URL="https://github.com/zubair-trabzada/geo-seo-claude.git"
CODEX_DIR="${HOME}/.codex"
SKILLS_DIR="${CODEX_DIR}/skills"
INSTALL_DIR="${SKILLS_DIR}/geo"
TEMP_DIR=$(mktemp -d)

# Detect if running via curl pipe (no interactive input available)
INTERACTIVE=true
if [ ! -t 0 ]; then
    INTERACTIVE=false
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   GEO-SEO Codex Skill Installer    ║${NC}"
    echo -e "${BLUE}║   GEO-First AI Search Optimization       ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}→ $1${NC}"
}

cleanup() {
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

main() {
    print_header

    # ---- Check Prerequisites ----
    print_info "Checking prerequisites..."

    # Check for Git
    if ! command -v git &> /dev/null; then
        print_error "Git is required but not installed."
        echo "  Install: https://git-scm.com/downloads"
        exit 1
    fi
    print_success "Git found: $(git --version)"

    # Check for Python 3
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [ -n "$PYTHON_VERSION" ]; then
            MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
            MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
                PYTHON_CMD="python"
            fi
        fi
    fi

    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python 3.8+ is required but not found."
        echo "  Install: https://www.python.org/downloads/"
        exit 1
    fi
    print_success "Python found: $($PYTHON_CMD --version)"

    # Check for Codex
    if ! command -v codex &> /dev/null; then
        print_warning "Codex CLI not found in PATH."
        echo "  This tool is intended for a Codex-compatible environment."
        echo "  Install Codex or copy the skills into an existing compatible setup."
        echo ""
        if [ "$INTERACTIVE" = true ]; then
            read -p "Continue installation anyway? (y/n): " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            print_info "Non-interactive mode — continuing anyway..."
        fi
    else
        print_success "Codex environment found"
    fi

    # ---- Create Directories ----
    print_info "Creating directories..."

    mkdir -p "$SKILLS_DIR"
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$INSTALL_DIR/scripts"
    mkdir -p "$INSTALL_DIR/schema"
    mkdir -p "$INSTALL_DIR/hooks"

    print_success "Directory structure created"

    # ---- Clone or Copy Repository ----
    print_info "Fetching GEO-SEO skill files..."

    # Check if running from the repo directory (local install)
    # BASH_SOURCE may be empty when piped via curl, so handle gracefully
    SCRIPT_DIR=""
    if [ -n "${BASH_SOURCE[0]:-}" ] && [ "${BASH_SOURCE[0]}" != "bash" ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || true
    fi

    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/.codex/skills/geo/SKILL.md" ]; then
        print_info "Installing from local directory..."
        SOURCE_DIR="$SCRIPT_DIR"
    else
        print_info "Cloning from repository..."
        git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" || {
            print_error "Failed to clone repository. Check your internet connection."
            exit 1
        }
        SOURCE_DIR="${TEMP_DIR}/repo"
    fi

    # ---- Install Main Skill ----
    print_info "Installing main GEO skill..."

    cp -r "$SOURCE_DIR/.codex/skills/geo/"* "$INSTALL_DIR/"
    print_success "Main skill installed → ${INSTALL_DIR}/"

    # ---- Install Sub-Skills ----
    print_info "Installing sub-skills..."

    SKILL_COUNT=0
    for skill_dir in "$SOURCE_DIR/.codex/skills"/*/; do
        if [ -d "$skill_dir" ]; then
            skill_name=$(basename "$skill_dir")
            target_dir="${SKILLS_DIR}/${skill_name}"
            mkdir -p "$target_dir"
            cp -r "$skill_dir"* "$target_dir/"
            SKILL_COUNT=$((SKILL_COUNT + 1))
            print_success "  ${skill_name}"
        fi
    done
    echo "  → ${SKILL_COUNT} sub-skills installed"

    # ---- Install Scripts ----
    print_info "Installing utility scripts..."

    if [ -d "$SOURCE_DIR/scripts" ]; then
        cp -r "$SOURCE_DIR/scripts/"* "$INSTALL_DIR/scripts/"
        chmod +x "$INSTALL_DIR/scripts/"*.py 2>/dev/null || true
        print_success "Scripts installed → ${INSTALL_DIR}/scripts/"
    fi

    # ---- Install Schema Templates ----
    print_info "Installing schema templates..."

    if [ -d "$SOURCE_DIR/schema" ]; then
        cp -r "$SOURCE_DIR/schema/"* "$INSTALL_DIR/schema/"
        print_success "Schema templates installed → ${INSTALL_DIR}/schema/"
    fi

    # ---- Install Hooks ----
    if [ -d "$SOURCE_DIR/hooks" ] && [ "$(ls -A "$SOURCE_DIR/hooks" 2>/dev/null)" ]; then
        print_info "Installing hooks..."
        cp -r "$SOURCE_DIR/hooks/"* "$INSTALL_DIR/hooks/"
        chmod +x "$INSTALL_DIR/hooks/"* 2>/dev/null || true
        print_success "Hooks installed → ${INSTALL_DIR}/hooks/"
    fi

    # ---- Install Python Dependencies ----
    print_info "Installing Python dependencies..."

    if [ -f "$SOURCE_DIR/requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r "$SOURCE_DIR/requirements.txt" --quiet 2>/dev/null && {
            print_success "Python dependencies installed"
        } || {
            print_warning "Some Python dependencies failed to install."
            echo "  Run manually: $PYTHON_CMD -m pip install -r requirements.txt"
            cp "$SOURCE_DIR/requirements.txt" "$INSTALL_DIR/"
        }
    fi

    # ---- Optional: Install Playwright ----
    if [ "$INTERACTIVE" = true ]; then
        echo ""
        read -p "Install Playwright for screenshots? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Installing Playwright browsers..."
            $PYTHON_CMD -m playwright install chromium 2>/dev/null && {
                print_success "Playwright Chromium installed"
            } || {
                print_warning "Playwright installation failed. Screenshots won't be available."
            }
        fi
    else
        print_info "Skipping Playwright (non-interactive mode). Install later with: python3 -m playwright install chromium"
    fi

    # ---- Verify Installation ----
    echo ""
    print_info "Verifying installation..."

    VERIFY_OK=true

    [ -f "$INSTALL_DIR/SKILL.md" ] && print_success "Main skill file" || { print_error "Main skill file missing"; VERIFY_OK=false; }
    [ -d "$SKILLS_DIR/geo-audit" ] && print_success "Sub-skills directory" || { print_error "Sub-skills missing"; VERIFY_OK=false; }
    [ -d "$INSTALL_DIR/scripts" ] && print_success "Utility scripts" || { print_error "Scripts missing"; VERIFY_OK=false; }
    [ -d "$INSTALL_DIR/schema" ] && print_success "Schema templates" || { print_error "Schema templates missing"; VERIFY_OK=false; }

    # ---- Print Summary ----
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Installation Complete!             ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Installed to: ${INSTALL_DIR}"
    echo "  Skills:       ${SKILL_COUNT} sub-skills"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  Run the analyzer directly:"
    echo ""
    echo "    $PYTHON_CMD run.py https://example.com"
    echo ""
    echo -e "${BLUE}Natural-language triggers:${NC}"
    echo "    audit this site for GEO and SEO"
    echo "    check AI crawler access for this domain"
    echo "    review schema, FAQ coverage, and entities"
    echo "    generate a client-ready GEO report"
    echo ""
    echo "  Documentation: https://github.com/zubair-trabzada/geo-seo-claude"
    echo ""
}

main "$@"
