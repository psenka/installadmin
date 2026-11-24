@echo off
chcp 65001 >nul
echo Starting InstallAdmin...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -e . >nul 2>&1
python -m install_admin.main