@echo off
rem Day trader desk: PAPER ONLY. Reruns the scan, rebuilds dashboard.html, opens it.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py -3
%PY% --version >nul 2>nul || (echo Python 3.8 or newer is needed. Install it from python.org, then run this again. & pause & exit /b 1)
%PY% run_pipeline.py TSLA,NVDA,SPY,QQQ
if errorlevel 1 (echo Something went wrong. Read the lines above. & pause)
start "" "%~dp0dashboard.html"
