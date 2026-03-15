#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="aguada-bridge-autoswitch.service"
SRC="/home/luc/Dev/espnow-ha/tools/systemd/${SERVICE_NAME}"
DST_DIR="$HOME/.config/systemd/user"
DST="${DST_DIR}/${SERVICE_NAME}"

mkdir -p "$DST_DIR"
cp "$SRC" "$DST"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"

echo "[ok] Service instalado e iniciado: $SERVICE_NAME"
echo "[status]"
systemctl --user --no-pager --full status "$SERVICE_NAME" | sed -n '1,12p'

echo
echo "Comandos úteis:"
echo "  systemctl --user status $SERVICE_NAME"
echo "  systemctl --user restart $SERVICE_NAME"
echo "  systemctl --user stop $SERVICE_NAME"
