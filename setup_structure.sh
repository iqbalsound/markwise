#!/usr/bin/env bash
# Creates the MarkWise folder structure and blank files.
# Safe to run more than once: existing files are NOT overwritten or emptied.
set -euo pipefail

# Make sure we are in the repository root (the folder that contains .git)
if [ ! -d ".git" ]; then
  echo "ERROR: run this script from inside your cloned markwise/ folder (the one with .git)."
  exit 1
fi

echo "Creating directories..."
mkdir -p src/markwise/db
mkdir -p src/markwise/auth
mkdir -p src/markwise/services
mkdir -p src/markwise/ui
mkdir -p src/markwise/assets/themes
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/ui
mkdir -p packaging/deb
mkdir -p .github/workflows

echo "Creating blank files..."

# Project root
touch .gitignore LICENSE README.md pyproject.toml requirements.txt requirements-dev.txt

# Package: src/markwise
touch src/markwise/__init__.py
touch src/markwise/app_info.py
touch src/markwise/paths.py
touch src/markwise/__main__.py
touch src/markwise/app.py

# db
touch src/markwise/db/__init__.py
touch src/markwise/db/models.py
touch src/markwise/db/session.py

# auth
touch src/markwise/auth/__init__.py
touch src/markwise/auth/passwords.py

# services
touch src/markwise/services/__init__.py
touch src/markwise/services/roster.py
touch src/markwise/services/files.py
touch src/markwise/services/pdf_reader.py
touch src/markwise/services/grader.py
touch src/markwise/services/pipeline.py
touch src/markwise/services/export.py
touch src/markwise/services/keystore.py

# ui
touch src/markwise/ui/__init__.py
touch src/markwise/ui/theme.py
touch src/markwise/ui/about.py
touch src/markwise/ui/login.py
touch src/markwise/ui/dialogs.py
touch src/markwise/ui/assessment_panel.py
touch src/markwise/ui/main_window.py

# themes
touch src/markwise/assets/themes/light.qss
touch src/markwise/assets/themes/dark.qss

# tests
touch tests/conftest.py
touch tests/unit/test_passwords.py
touch tests/unit/test_roster.py
touch tests/unit/test_files.py
touch tests/unit/test_grader.py
touch tests/integration/test_pipeline.py
touch tests/ui/test_login_dialog.py
touch tests/ui/test_theme_about.py

# packaging
touch packaging/launcher.py
touch packaging/markwise.spec
touch packaging/make_icon.py
touch packaging/build_deb.sh
touch packaging/deb/control.in
touch packaging/deb/markwise.desktop
touch packaging/deb/copyright
# NOTE: packaging/deb/markwise.png is NOT created here. It is a picture, not a text
# file, and is generated in Phase 10 by:  python packaging/make_icon.py

# GitHub Actions
touch .github/workflows/ci.yml
touch .github/workflows/release.yml

# build_deb.sh must be runnable on Linux
chmod +x packaging/build_deb.sh

echo ""
echo "Done. Files and folders created:"
find . -path ./.git -prune -o -path ./.venv -prune -o -type f -print | sort
