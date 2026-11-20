@echo off
REM Rulează scraperul Hot Wheels cu dublu-click.
REM Setările (chei Supabase/Resend, SCRAPERS, DRY_RUN, PAGE_DELAY) se citesc din .env.

title Hot Wheels Scraper
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

REM rulează din folderul în care e fișierul, oriunde l-ai deschide
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python check_hotwheels.py %*
) else (
    py check_hotwheels.py %*
)

echo.
if %errorlevel%==0 (
    echo Gata.
) else (
    echo Rularea s-a terminat cu erori ^(vezi mai sus^).
)
echo.
pause
