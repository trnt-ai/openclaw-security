#!/bin/bash
# Copyright (c) 2025-2026 Trent AI. All rights reserved.
# Install and set up Trent security audit for OpenClaw.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/trnt-ai/openclaw-security/main/install.sh | bash
#
# What this does:
#   1. Installs uv (Python package manager) if not already present
#   2. Installs trentai-mcp CLI via uv
#   3. Prompts for API key and runs openclaw-trent-setup

set -euo pipefail

UV_VERSION="0.7.2"

info() { printf "\033[1;34m%s\033[0m\n" "$1"; }
success() { printf "\033[1;32m%s\033[0m\n" "$1"; }
error() { printf "\033[1;31m%s\033[0m\n" "$1" >&2; }

# --- Check prerequisites ---

if ! command -v curl &> /dev/null; then
    error "curl is required but not found. Install it first."
    exit 1
fi

# --- Install uv if needed ---

if command -v uv &> /dev/null; then
    info "uv is already installed: $(uv --version)"
else
    info "Installing uv ${UV_VERSION}..."
    curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | sh

    # Source the env to pick up uv in current shell
    if [ -f "$HOME/.local/bin/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.local/bin/env"
    elif [ -f "$HOME/.cargo/env" ]; then
        # shellcheck disable=SC1091
        . "$HOME/.cargo/env"
    fi

    if ! command -v uv &> /dev/null; then
        export PATH="$HOME/.local/bin:$PATH"
    fi

    if ! command -v uv &> /dev/null; then
        error "uv installation failed. Install manually: https://docs.astral.sh/uv/"
        exit 1
    fi

    success "uv installed: $(uv --version)"
fi

# --- Install trentai-mcp ---

info "Installing trentai-mcp..."
uv tool install --upgrade trentai-mcp

if ! command -v openclaw-trent-setup &> /dev/null; then
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v openclaw-trent-setup &> /dev/null; then
    error "Installation succeeded but openclaw-trent-setup not found in PATH."
    error "Add ~/.local/bin to your PATH and try again."
    exit 1
fi

success "trentai-mcp installed!"

if command -v trent-openclaw-sysinfo &> /dev/null; then
    success "System analysis tool available: trent-openclaw-sysinfo"
fi

if command -v trent-openclaw-package-skills &> /dev/null; then
    success "Skill packaging tool available: trent-openclaw-package-skills"
fi

# --- Get API key ---

if [ -r /dev/tty ]; then
    echo ""
    info "You need a Trent API key to continue."
    echo "  If you don't have one, visit https://app.trent.ai to generate one."
    echo "  Log out if you don't see the 'Get OpenClaw Access' button."
    echo ""

    printf "Paste your API key: " > /dev/tty
    read -r API_KEY < /dev/tty
    echo "" > /dev/tty
else
    error "No TTY available. Run: openclaw-trent-setup --api-key <key>"
    exit 0
fi

if [ -z "$API_KEY" ]; then
    error "No API key provided. Run openclaw-trent-setup --api-key <key> when ready."
    exit 1
fi

# --- Run setup ---

# Ask if user wants to run the initial security audit
RUN_AUDIT="no"
if [ -r /dev/tty ]; then
    printf "Run a security audit now? [y/N] " > /dev/tty
    read -r RUN_AUDIT < /dev/tty
fi

if [[ "$RUN_AUDIT" =~ ^[Yy]$ ]]; then
    openclaw-trent-setup --api-key "$API_KEY" --yes
else
    openclaw-trent-setup --api-key "$API_KEY" --yes --skip-audit
    echo ""
    info "To run an audit later: trent-openclaw-audit"
fi
