#!/data/data/com.termux/files/usr/bin/bash
# Configurare o singură dată pe telefon (Termux). Rulează din Termux:
#   bash ~/storage/shared/Documents/hw-scraper/termux/setup.sh
#
# Face:
#   1. instalează Python și bibliotecile
#   2. pune scurtătura "hw-scraper" pentru widget-ul Termux:Widget
#   3. programează rularea automată din 2 în 2 ore (cron)
#   4. pornește programarea automat după restart (Termux:Boot)
set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUN_SCRIPT="$PROJECT_DIR/termux/run.sh"
echo "Proiect: $PROJECT_DIR"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "ATENTIE: lipseste $PROJECT_DIR/.env (copiaza-l de pe PC). Continui oricum."
fi

echo "== 1/4 Pachete =="
pkg update -y
pkg install -y python cronie termux-services
pip install -r "$PROJECT_DIR/requirements.txt"

echo "== 2/4 Widget =="
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/hw-scraper <<EOF
#!/data/data/com.termux/files/usr/bin/bash
bash "$RUN_SCRIPT"
echo
read -p "Gata. Apasa Enter ca sa inchizi."
EOF
chmod +x ~/.shortcuts/hw-scraper

echo "== 3/4 Rulare automata din 2 in 2 ore =="
CRON_LINE="0 */2 * * * /data/data/com.termux/files/usr/bin/bash \"$RUN_SCRIPT\" >> \"$HOME/hw-scraper.log\" 2>&1"
( crontab -l 2>/dev/null | grep -v "hw-scraper" || true; echo "$CRON_LINE # hw-scraper" ) | crontab -
# termux-services are nevoie de o sesiune noua ca sa porneasca; o pornim si direct
sv-enable crond 2>/dev/null || true
pgrep crond >/dev/null || crond

echo "== 4/4 Pornire dupa restart =="
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/hw-scraper.sh <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
pgrep crond >/dev/null || crond
EOF
chmod +x ~/.termux/boot/hw-scraper.sh
termux-wake-lock || true

echo
echo "Gata! Mai ai de facut:"
echo " - adauga widget-ul Termux:Widget pe ecran (apare 'hw-scraper')"
echo " - deschide o data aplicatia Termux:Boot"
echo " - Setari > Baterie: Termux si Termux:Boot la 'Nerestrictionat' / 'nu intra niciodata in repaus'"
echo "Log rulari automate: tail -50 ~/hw-scraper.log"
