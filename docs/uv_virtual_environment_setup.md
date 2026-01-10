# Setting Up Python Virtual Environments with `uv`

## Overview

`uv` is a high-performance Python package and project manager written in Rust. It provides significantly faster package installation and virtual environment management compared to traditional tools like `pip` and `venv`. This guide covers the complete setup and usage of `uv` for creating and managing Python virtual environments.

## 1. Installation

### On macOS and Linux

Install `uv` using the official installer script:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This command downloads and installs `uv` on your system.

### On Windows

Open PowerShell with administrative privileges and execute:

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

## 2. Creating a Virtual Environment

### Basic Environment Creation

Navigate to your project directory and create a virtual environment:

```bash
# Create a virtual environment in .venv directory (recommended)
uv venv

# Or create with a specific name
uv venv my-project-env
```

The `uv venv` command creates an isolated Python environment in the `.venv` directory within your project.

### Specifying Python Version

Create a virtual environment with a specific Python version:

```bash
# Create with Python 3.8
uv venv --python 3.8

# Create with Python 3.11 (latest stable)
uv venv --python 3.11

# Create with Python 3.12
uv venv --python 3.12
```

### Custom Environment Location

You can specify a custom location for your virtual environment:

```bash
# Create environment in a custom directory
uv venv /path/to/my/custom/venv
```

## 3. Activating the Virtual Environment

### On macOS and Linux

```bash
# Activate the default .venv environment
source .venv/bin/activate

# Or activate a custom named environment
source my-project-env/bin/activate
```

### On Windows (PowerShell)

```powershell
# Activate the default .venv environment
.venv\Scripts\Activate.ps1

# Or activate a custom named environment
my-project-env\Scripts\Activate.ps1
```

### On Windows (Command Prompt)

```cmd
# Activate the default .venv environment
.venv\Scripts\activate.bat

# Or activate a custom named environment
my-project-env\Scripts\activate.bat
```

## 4. Deactivating the Virtual Environment

To exit the virtual environment and return to your global Python environment:

```bash
# Works on all platforms
deactivate
```

## 5. Package Management

### Installing Packages

With the virtual environment activated, install packages using `uv`'s pip interface:

```bash
# Install a single package
uv pip install numpy

# Install multiple packages
uv pip install pandas matplotlib scikit-learn

# Install from a requirements.txt file
uv pip install -r requirements.txt
```

### Listing Installed Packages

```bash
# List all installed packages
uv pip list

# Or use the traditional pip command
pip list
```

### Upgrading Packages

```bash
# Upgrade a specific package
uv pip install --upgrade numpy

# Upgrade all packages
uv pip install --upgrade -r requirements.txt
```

### Removing Packages

```bash
# Remove a specific package
uv pip uninstall numpy

# Remove multiple packages
uv pip uninstall pandas matplotlib
```

### Freezing Dependencies

Create a `requirements.txt` file with the current environment's packages:

```bash
# Freeze current environment to requirements.txt
uv pip freeze > requirements.txt

# Freeze to a specific file
uv pip freeze > requirements-dev.txt
```

## 6. Environment Variables and Project Configuration

### Automatic Environment Activation

For convenience, you can configure your shell to automatically activate the virtual environment when entering the project directory. Add this to your `.bashrc` or `.zshrc`:

```bash
# Auto-activate virtual environment
function auto_activate_venv {
    if [[ -d ".venv" && -z "$VIRTUAL_ENV" ]]; then
        source .venv/bin/activate
        echo "Activated virtual environment: $(basename $VIRTUAL_ENV)"
    fi
}

# Run on directory change
cd() {
    builtin cd "$@"
    auto_activate_venv
}
```

### Project-Specific Configuration

Create a `pyproject.toml` file for project configuration:

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My Python project"
dependencies = [
    "pandas>=2.0.0",
    "matplotlib>=3.7.0",
    "scikit-learn>=1.3.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]
```

## 7. Best Practices

### Environment Management

1. **Use `.venv` as the standard directory name**: This is the conventional name and is often hidden from version control systems by default.

2. **Activate environments consistently**: Always activate your virtual environment before working on your project to ensure you're using the correct Python version and packages.

3. **Pin dependency versions**: Use exact version numbers in `requirements.txt` or `pyproject.toml` for reproducible environments:

   ```txt
   pandas==2.0.3
   matplotlib==3.7.2
   ```

4. **Separate development dependencies**: Use separate requirements files for production and development dependencies:

   ```bash
   # Production dependencies
   uv pip freeze > requirements.txt

   # Development dependencies
   uv pip install pytest black flake8
   uv pip freeze > requirements-dev.txt
   ```

### Project Structure

Follow a consistent project structure:

```
my-project/
├── .venv/                    # Virtual environment (gitignored)
├── src/                      # Source code
│   └── my_package/
├── tests/                    # Test files
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── pyproject.toml           # Project configuration
└── README.md                # Project documentation
```

### Performance Tips

1. **Use `uv` for faster installations**: `uv` is significantly faster than `pip` for package installation and environment creation.

2. **Parallel installations**: `uv` automatically installs packages in parallel when possible.

3. **Dependency caching**: `uv` caches downloaded packages to speed up subsequent installations.

## 8. Troubleshooting

### Common Issues

**Issue**: `uv: command not found`
**Solution**: Ensure `uv` is properly installed and added to your PATH. You may need to restart your terminal or source your shell configuration file.

**Issue**: Permission denied when creating virtual environment
**Solution**: Ensure you have write permissions to the target directory, or use `sudo` if necessary (not recommended).

**Issue**: Packages not available after activation
**Solution**: Ensure you're running commands from within the activated virtual environment. Check that the environment is properly activated by looking for `(venv)` in your terminal prompt.

**Issue**: Python version conflicts
**Solution**: Specify the exact Python version when creating the virtual environment using `uv venv --python 3.x`.

### Getting Help

```bash
# View uv help
uv --help

# View specific command help
uv venv --help
uv pip --help

# Check uv version
uv --version
```

## 9. Migration from pip/venv

If you're migrating from traditional `pip` and `venv`, here's a quick comparison:

| Traditional | uv |
|-------------|----|
| `python -m venv .venv` | `uv venv` |
| `source .venv/bin/activate` | `source .venv/bin/activate` |
| `pip install package` | `uv pip install package` |
| `pip freeze > requirements.txt` | `uv pip freeze > requirements.txt` |

The main differences are:
- `uv venv` creates environments faster than `python -m venv`
- `uv pip` commands are faster than `pip` commands
- All other activation and usage patterns remain the same

## 10. Integration with Development Tools

### IDE Integration

Most modern IDEs automatically detect and suggest virtual environment activation:

- **VS Code**: The Python extension will prompt to select a virtual environment
- **PyCharm**: Automatically detects `.venv` directory
- **Vim/Neovim**: Configure your `.vimrc` or use plugins like `vim-virtualenv`

### Git Integration

Add these lines to your `.gitignore` file:

```gitignore
# Virtual environments
.venv/
venv/
env/
ENV/

# Python cache
__pycache__/
*.pyc
*.pyo
```

## Summary

`uv` provides a modern, fast alternative to traditional Python virtual environment management. Key benefits include:

- **Faster package installation** (often 10-100x faster than pip)
- **Better dependency resolution**
- **Improved caching** for repeated installations
- **Drop-in compatibility** with existing pip workflows

By following this guide, you can efficiently set up and manage Python virtual environments for your projects using `uv`.
