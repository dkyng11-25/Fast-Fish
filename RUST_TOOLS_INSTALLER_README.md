# Rust-based Tools Installer

**File**: `install_rust_tools.sh`
**Purpose**: Simple bash script to install recommended Rust-based tools using Homebrew
**Based on**: `.cursor/rules/commands.mdc` recommendations

---

## 🚀 **Quick Start**

### **Run the Installer**
```bash
# Make executable (if not already)
chmod +x install_rust_tools.sh

# Run the installer
./install_rust_tools.sh
```

### **What It Installs**

The script installs the following Rust-based tools recommended in `commands.mdc`:

| Tool | Purpose | Command | Description |
|------|---------|---------|-------------|
| **eza** | File listing | `eza` | Modern replacement for `ls` and `tree` |
| **ripgrep** | Text search | `rg` | Fast search tool (replacement for `grep`) |
| **skim** | Fuzzy finder | `sk` | Interactive fuzzy finder (replacement for `fzf`) |
| **choose** | Text processing | `choose` | Human-friendly alternative to `cut` and `awk` |
| **procs** | Process monitoring | `procs` | Modern replacement for `ps` and `top` |
| **tokei** | Code counting | `tokei` | Fast code counter (replacement for `wc`) |
| **bat** | File viewing | `bat` | Cat clone with syntax highlighting |
| **fd** | File finding | `fd` | Simple, fast alternative to `find` |
| **navi** | Cheatsheets | `navi` | Interactive cheatsheet tool |

---

## 🔧 **Features**

### **Automatic Homebrew Installation**
- Installs Homebrew if not present
- Configures PATH for Linux/WSL users
- Updates Homebrew before installing tools

### **Smart Installation**
- Checks if tools are already installed
- Only installs missing tools
- Provides clear status messages
- Handles installation errors gracefully

### **Cross-Platform Support**
- Works on macOS, Linux, and WSL
- Automatically detects OS and configures accordingly
- Handles different Homebrew installation paths

---

## 📋 **Prerequisites**

### **System Requirements**
- Bash shell
- Internet connection
- sudo access (for Homebrew installation)

### **Supported Platforms**
- ✅ **macOS** (Intel and Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, CentOS, etc.)
- ✅ **WSL** (Windows Subsystem for Linux)

---

## 🎯 **Usage Examples**

### **Basic Installation**
```bash
./install_rust_tools.sh
```

### **Check What's Installed**
```bash
# After installation, check tool versions
eza --version
rg --version
sk --version
choose --version
procs --version
tokei --version
bat --version
fd --version
navi --version
```

### **Verify Installation**
```bash
# Check if all tools are available
which eza rg sk choose procs tokei bat fd navi
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Permission Denied**
```bash
# Make script executable
chmod +x install_rust_tools.sh
```

#### **2. Homebrew Not Found After Installation**
```bash
# For Linux/WSL users, add to your shell profile
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
source ~/.bashrc
```

#### **3. Tools Not Found After Installation**
```bash
# Restart your terminal or source your profile
source ~/.bashrc
# or
exec $SHELL
```

#### **4. Installation Fails**
```bash
# Update Homebrew and try again
brew update
brew upgrade
./install_rust_tools.sh
```

---

## 📊 **Tool Usage Examples**

### **File Operations**
```bash
# List files with eza (replacement for ls)
eza -la --tree --level=2

# Find files with fd (replacement for find)
fd "*.py" --type f

# View files with bat (replacement for cat)
bat requirements.txt
```

### **Text Processing**
```bash
# Search with ripgrep (replacement for grep)
rg "import pandas" --type py

# Fuzzy find with skim (replacement for fzf)
sk

# Extract columns with choose (replacement for cut/awk)
cat data.csv | choose 1,3,5
```

### **System Monitoring**
```bash
# Monitor processes with procs (replacement for ps/top)
procs --pager disable

# Count code with tokei (replacement for wc)
tokei src/ tests/
```

### **Interactive Tools**
```bash
# Use navi for cheatsheets
navi
```

---

## 🎨 **Customization**

### **Modify Tool List**
Edit the `tools` array in the script to add/remove tools:

```bash
# Add your own tools
declare -A tools=(
    ["eza"]="eza"
    ["ripgrep"]="ripgrep"
    # Add more tools here
    ["your_tool"]="your_brew_package"
)
```

### **Add Tool Aliases**
Create aliases in your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias ll='eza -la'
alias tree='eza --tree'
alias grep='rg'
alias find='fd'
alias cat='bat'
alias ps='procs'
alias wc='tokei'
```

---

## ✅ **Verification**

After installation, verify all tools work:

```bash
# Test each tool
eza --version && echo "✓ eza working"
rg --version && echo "✓ ripgrep working"
sk --version && echo "✓ skim working"
choose --version && echo "✓ choose working"
procs --version && echo "✓ procs working"
tokei --version && echo "✓ tokei working"
bat --version && echo "✓ bat working"
fd --version && echo "✓ fd working"
navi --version && echo "✓ navi working"
```

---

## 📝 **Notes**

- **Homebrew Required**: This script uses Homebrew for all installations
- **Rust Tools**: All tools are written in Rust for maximum performance
- **Cross-Platform**: Works on macOS, Linux, and WSL
- **Safe Installation**: Checks for existing installations before installing
- **Error Handling**: Gracefully handles installation failures

---

**Created**: 2025-09-25
**Version**: 1.0
**Status**: Ready to Use
