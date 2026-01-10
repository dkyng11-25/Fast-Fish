#!/bin/bash

# Rust-based Tools Installer
# Installs recommended Rust tools using Homebrew
# Based on commands.mdc recommendations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Homebrew is installed
check_homebrew() {
    if ! command_exists brew; then
        print_error "Homebrew is not installed!"
        print_status "Installing Homebrew..."
        
        # Install Homebrew
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Add Homebrew to PATH for Linux/WSL
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
            eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        fi
        
        print_success "Homebrew installed successfully!"
    else
        print_success "Homebrew is already installed."
    fi
}

# Function to update Homebrew
update_homebrew() {
    print_status "Updating Homebrew..."
    brew update
    print_success "Homebrew updated!"
}

# Function to install a tool if not already installed
install_tool() {
    local tool="$1"
    local brew_name="$2"
    
    if command_exists "$tool"; then
        print_success "$tool is already installed."
    else
        print_status "Installing $tool..."
        if brew install "$brew_name"; then
            print_success "$tool installed successfully!"
        else
            print_error "Failed to install $tool"
            return 1
        fi
    fi
}

# Main installation function
main() {
    print_status "Starting Rust-based tools installation..."
    print_status "Based on commands.mdc recommendations"
    echo
    
    # Check and install Homebrew
    check_homebrew
    echo
    
    # Update Homebrew
    update_homebrew
    echo
    
    # Define tools to install (tool_name:brew_package_name)
    declare -A tools=(
        ["eza"]="eza"                    # Modern replacement for 'ls' and 'tree'
        ["rg"]="ripgrep"                 # Fast search tool (ripgrep)
        ["sk"]="skim"                    # Fuzzy finder (skim)
        ["choose"]="choose"              # Human-friendly and fast alternative to cut
        ["procs"]="procs"                # Modern replacement for 'ps' and 'top'
        ["tokei"]="tokei"                # Fast code counter (replacement for 'wc')
        ["bat"]="bat"                    # Cat clone with syntax highlighting
        ["fd"]="fd"                      # Simple, fast alternative to 'find'
        ["navi"]="navi"                  # Interactive cheatsheet tool
    )
    
    print_status "Installing Rust-based tools..."
    echo
    
    # Install each tool
    for tool in "${!tools[@]}"; do
        install_tool "$tool" "${tools[$tool]}"
    done
    
    echo
    print_success "All Rust-based tools installation completed!"
    echo
    
    # Display installed tools
    print_status "Installed tools:"
    for tool in "${!tools[@]}"; do
        if command_exists "$tool"; then
            local version=$(command "$tool" --version 2>/dev/null | head -n1 || echo "version unknown")
            print_success "✓ $tool: $version"
        else
            print_warning "✗ $tool: installation may have failed"
        fi
    done
    
    echo
    print_status "You may need to restart your terminal or run 'source ~/.bashrc' to use the new tools."
    print_status "For Linux/WSL users, make sure Homebrew is in your PATH:"
    print_status "  eval \"\$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\""
}

# Run main function
main "$@"
