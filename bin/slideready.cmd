@echo off
rem SlideReady komut satırı (Windows): bin\slideready doctor | analyze | preview | export
set "PYTHONPATH=%~dp0..;%PYTHONPATH%"
python -m slideready %*
