@echo off
chcp 65001 >nul
echo Starting InstallAdmin...
set PYTHONPATH=src
python src/install_admin/main.py