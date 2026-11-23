#!/data/data/com.termux/files/usr/bin/bash
# Rulează scraperul o dată. Îl folosesc și widget-ul, și rularea automată (cron).
# cron pornește cu un PATH minimal
export PATH="/data/data/com.termux/files/usr/bin:$PATH"
cd "$(dirname "$0")/.." || exit 1
echo "=== $(date '+%Y-%m-%d %H:%M') ==="
python check_hotwheels.py "$@"

# păstrează log-ul mic: ultimele ~2000 de rânduri
LOG="$HOME/hw-scraper.log"
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 3000 ]; then
    tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
