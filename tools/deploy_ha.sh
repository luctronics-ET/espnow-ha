#!/usr/bin/env bash
# =============================================================================
# deploy_ha.sh — Copia arquivos homeassistant/ para /config no HAOS via Samba
# e dispara verificação + reinício do HA via REST API.
#
# USO:
#   chmod +x tools/deploy_ha.sh
#   SAMBA_PASS=SUA_SENHA ./tools/deploy_ha.sh
#
# Para encontrar a senha do Samba:
#   HA → Configurações → Addons → Samba share → Configuração → campo "password"
# =============================================================================
set -euo pipefail

# ── Configuração ──────────────────────────────────────────────────────────────
HA_HOST="192.168.0.177"
HA_PORT="8123"
SAMBA_USER="${SAMBA_USER:-homeassistant}"
SAMBA_PASS="${SAMBA_PASS:-}"          # passar via env: SAMBA_PASS=xxx ./deploy_ha.sh
HA_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4YTgyOGNmMWFiYzE0NWRmOGI0MmIyNGIyYWYyYmMxNyIsImlhdCI6MTc3MzM1OTY0OCwiZXhwIjoyMDg4NzE5NjQ4fQ.DnjrZ9n5y--OcU3w9deDtz37vDDsG92EoULehczM_lo"
REPO_HA_DIR="$(cd "$(dirname "$0")/../homeassistant" && pwd)"
# Arquivos a copiar para /config (raiz do config share)
HA_CONFIG_FILES=(
  configuration.yaml
  automations.yaml
  template_sensors.yaml
  statistics_sensors.yaml
  input_boolean.yaml
  input_button.yaml
  input_datetime.yaml
  input_number.yaml
  input_select.yaml
  input_text.yaml
  dashboard.yaml
  mqtt_gateway_sensors.yaml
)

# ── Verificações iniciais ─────────────────────────────────────────────────────
if [[ -z "$SAMBA_PASS" ]]; then
  echo "ERRO: defina SAMBA_PASS antes de executar."
  echo "  SAMBA_PASS=SUA_SENHA ./tools/deploy_ha.sh"
  exit 1
fi

if ! command -v smbclient &>/dev/null; then
  echo "ERRO: smbclient não instalado. Instale com: sudo apt install smbclient"
  exit 1
fi

echo "──────────────────────────────────────────────────────────"
echo " Deploy Aguada HA → $HA_HOST"
echo " Usuário Samba: $SAMBA_USER"
echo " Origem: $REPO_HA_DIR"
echo "──────────────────────────────────────────────────────────"

# Testa conexão Samba
echo "[1/4] Testando conexão Samba..."
smbclient "//$HA_HOST/config" -U "$SAMBA_USER%$SAMBA_PASS" -c "ls" > /dev/null 2>&1 \
  || { echo "ERRO: credenciais Samba inválidas ou share inacessível."; exit 1; }
echo "  ✅ Samba OK"

# ── Copia arquivos ────────────────────────────────────────────────────────────
echo "[2/4] Copiando arquivos para /config..."
for file in "${HA_CONFIG_FILES[@]}"; do
  src="$REPO_HA_DIR/$file"
  if [[ ! -f "$src" ]]; then
    echo "  ⚠️  Arquivo não encontrado, pulando: $file"
    continue
  fi
  smbclient "//$HA_HOST/config" -U "$SAMBA_USER%$SAMBA_PASS" \
    -c "put \"$src\" \"$file\"" > /dev/null 2>&1 \
    && echo "  ✅ $file" \
    || echo "  ❌ FALHA: $file"
done

# ── Verificar configuração via API ────────────────────────────────────────────
echo "[3/4] Verificando configuração do HA..."
CHECK=$(curl -s -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  "http://$HA_HOST:$HA_PORT/api/config/core/check_config")
RESULT=$(echo "$CHECK" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('result','?'), '|', d.get('errors',''))" 2>/dev/null || echo "erro ao parsear resposta")
echo "  Resultado: $RESULT"
if echo "$RESULT" | grep -qi "invalid\|error"; then
  echo "  ❌ Configuração inválida — corrigir antes de reiniciar."
  echo "  Resposta completa: $CHECK"
  exit 1
fi
echo "  ✅ Configuração válida"

# ── Reiniciar HA ──────────────────────────────────────────────────────────────
echo "[4/4] Reiniciando Home Assistant..."
curl -s -X POST \
  -H "Authorization: Bearer $HA_TOKEN" \
  -H "Content-Type: application/json" \
  "http://$HA_HOST:$HA_PORT/api/services/homeassistant/restart" \
  --data "{}" > /dev/null
echo "  ✅ Reinício solicitado — aguarde ~60s para o HA voltar."
echo ""
echo "  Dashboard disponível em: http://$HA_HOST:$HA_PORT"
echo "──────────────────────────────────────────────────────────"
echo " Deploy concluído"
echo "──────────────────────────────────────────────────────────"
