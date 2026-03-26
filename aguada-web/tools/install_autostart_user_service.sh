#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
UNIT_TEMPLATE="$SCRIPT_DIR/systemd/aguada-web-backend.service"
DST_DIR="$HOME/.config/systemd/user"
SERVICE_NAME="aguada-web-backend.service"
DST_PATH="$DST_DIR/$SERVICE_NAME"

mkdir -p "$DST_DIR"
sed "s#__PROJECT_ROOT__#$PROJECT_ROOT#g" "$UNIT_TEMPLATE" > "$DST_PATH"

systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME"

if loginctl enable-linger "$USER" >/dev/null 2>&1; then
  echo "[ok] Linger ativado para $USER"
else
  echo "[warn] Não foi possível ativar linger automaticamente. Se quiser autostart sem login ativo, rode: sudo loginctl enable-linger $USER"
fi

echo "[ok] Unit instalada e iniciada: $SERVICE_NAME"
echo "[status]"
systemctl --user --no-pager --full status "$SERVICE_NAME" | sed -n '1,12p'

echo
echo "Comandos úteis:"
echo "  systemctl --user status $SERVICE_NAME"
echo "  systemctl --user restart $SERVICE_NAME"
echo "  systemctl --user stop $SERVICE_NAME"
