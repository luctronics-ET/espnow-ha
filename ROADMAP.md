# Aguada — Roadmap & Status

> Este arquivo é a interface principal de comunicação entre o usuário, agentes e sessões futuras.
> Atualize ao iniciar/concluir fases. A especificação completa está em `AGUADA_SYSTEM_DOC.md`.

---

## Estado Atual — 2026-03-12

Firmware base escrito do zero seguindo o protocolo v3.2. Ainda não compilado/testado em hardware.

---

## Fases

### Fase 1 — Firmware Node (sensor + relay + NVS boot)
**Status: ✅ Escrito** — não testado em hardware

Arquivos:
- `firmware/node/src/main.cpp` — loop principal, modo sensor/relay, boot NVS
- `firmware/node/src/nvs_config.cpp` — leitura/gravação NVS
- `firmware/node/src/ultrasonic.cpp` — driver HC-SR04
- `firmware/node/src/sensor_filter.cpp` — outlier reject + média móvel
- `firmware/node/src/espnow_radio.cpp` — ESP-NOW init, CRC-16 tx/rx
- `firmware/node/src/mesh.cpp` — tabela de vizinhos, relay, score

Pendente:
- [ ] Compilar com `pio run` no ESP32-C3
- [ ] Testar leitura HC-SR04 em bancada
- [ ] Verificar gravação NVS e boot relay vs sensor

---

### Fase 2 — Protocolo Binário v3 + CRC-16
**Status: ✅ Implementado**

- `firmware/shared/protocol.h` — struct 16 bytes, static_assert, todos os tipos/flags
- CRC-16/CCITT em `crc16.h` (node e gateway têm cópia local)

Pendente:
- [ ] Teste de loopback: node → gateway → verificar JSON no serial

---

### Fase 3 — Filtros
**Status: ✅ Implementado**

- Layer 1: rejeição de outlier (delta > `filter_outlier_cm`)
- Layer 2: média móvel (janela `filter_window`)
- Layer 3: threshold de envio (`filter_threshold_cm`) + envio forçado + heartbeat

Pendente:
- [ ] Validar com sensor real em superfície de água

---

### Fase 4 — Gateway USB + JSON Serial
**Status: ✅ Escrito** — não testado

- `firmware/gateway/src/main.cpp` — recebe ESP-NOW, serializa JSON, parseia comandos
- `firmware/gateway/src/espnow_gw.cpp` — CRC verify, cache de MACs por node_id
- Tempo: bridge.py envia `{"cmd":"SETTIME","ts":...}` no startup

Pendente:
- [ ] Compilar com `pio run` no ESP32-S3
- [ ] Testar output JSON no serial monitor
- [ ] Verificar cache MAC para comandos unicast

---

### Fase 5 — bridge.py + MQTT + HA Discovery
**Status: ✅ Escrito** — não testado

- `tools/bridge.py` — lê serial, calcula level/volume, publica MQTT, HA Discovery
- `tools/reservoirs.yaml` — parâmetros dos 5 nodes CMASM
- `tools/nvs_tool.py` — CLI para enviar CONFIG/RESTART via gateway

Pendente:
- [ ] Testar com gateway real conectado
- [ ] Verificar entidades no Home Assistant após HELLO
- [ ] Testar timeout offline (padrão 300s)

---

### Fase 6 — CMD_CONFIG via ESP-NOW
**Status: 🟠 Parcial**

Gateway envia `PKT_CMD_CONFIG` com `FLAG_CONFIG_PENDING`. Node reinicia ao receber.
Full transfer de `node_config_t` ainda não implementado (precisa protocolo extendido ou OTA-style).

Pendente:
- [ ] Definir protocolo de transferência de config completa
- [ ] Implementar no gateway e node

---

### Fase 7 — Mesh Relay + Tabela de Vizinhos
**Status: ✅ Escrito** — não testado

- `mesh.cpp`: atualiza vizinhos ao receber qualquer pacote, expira por timeout
- Node em modo relay (`num_sensors=0`) retransmite com TTL decrement + dedup por seq
- Score: `rssi - hops_to_gw × 10`

Pendente:
- [ ] Testar topologia CMASM com 2+ nodes

---

### Fase 8 — OTA via ESP-NOW
**Status: ⬜ Não iniciado**

Protocolo definido no spec (PKT_OTA_BLOCK, PKT_OTA_END + SHA-256).
Partições `app0`/`app1` já configuradas em `partitions.csv`.

---

### Fase 9 — Deep Sleep (bateria)
**Status: ⬜ Não iniciado**

Incompatível com modo relay. NVS flag `deep_sleep_enabled`.

---

### Fase 10 — Balanço Hídrico + Dashboard HA
**Status: ⬜ Não iniciado**

Cálculo: `volume(18h) - volume(06h)`. Alerta de vazamento por limiar.
Dashboard: cards HA com nível, %, volume, RSSI por reservatório.

---

### Fase 11 — PoC ESPHome (avaliação de migração)
**Status: 🟠 Planejado**

Objetivo: decidir com evidências se vale migrar parte do sistema para ESPHome sem perder robustez da malha ESP-NOW.

Escopo do PoC (2 trilhas):
- **Trilha A (híbrida, recomendada):** manter node/gateway/bridge atuais e integrar ESPHome via MQTT/HA para controle/UX.
- **Trilha B (experimental):** 1 nó com ESPHome (Wi-Fi + OTA + deep sleep + sensor ultrassônico) para comparação direta.

Métricas de comparação (coletar por no mínimo 72h):
- Confiabilidade de telemetria: `% de mensagens recebidas` e gaps > 2× intervalo nominal.
- Consumo energético: estimativa de autonomia por bateria (mesma célula e duty-cycle).
- Latência ponta a ponta: medição → entidade HA atualizada.
- Estabilidade OTA: taxa de sucesso e tempo médio de atualização.
- Manutenção: tempo para configurar novo nó e tempo de troubleshooting.

Critério de decisão (Go/No-Go):
- **Go parcial (adoção híbrida):** se ESPHome reduzir esforço operacional sem piorar confiabilidade (>98% entrega) nem autonomia de forma relevante.
- **No-Go para migração total:** se mesh/relay/consumo ficarem piores que o stack atual ESP-NOW.

Entregáveis:
- Relatório curto com tabela comparativa A vs B.
- Recomendação final: manter atual, híbrido, ou plano de migração por fases.
- Lista de riscos (especialmente ESP-NOW mesh, OTA e deep sleep simultâneos).

---

## Próximas Ações Imediatas

1. **Compilar node** — `cd firmware/node && pio run`
2. **Compilar gateway** — `cd firmware/gateway && pio run`
3. **Primeiro teste integrado** — node + gateway + bridge.py + HA
4. **Iniciar PoC ESPHome (trilha A)** — criar 1 device ESPHome para consumir/publicar MQTT `aguada/...`
5. **Planejar trilha B** — preparar 1 nó experimental ESPHome para benchmark de 72h

---

## Notas de Arquitetura

- `AGUADA_SYSTEM_DOC.md` é o spec canônico — não alterar comportamento sem refletir lá
- Parâmetros de reservatório **nunca** vão para o node — ficam em `reservoirs.yaml`
- node_id = 2 últimos bytes do MAC — sem cadastro manual
- `.delete/` e `.*_old/` são ignorados pelo git e pelo build

---

## Problemas Conhecidos / Decisões Pendentes

| # | Descrição | Decisão pendente |
|---|-----------|-----------------|
| 1 | CMD_CONFIG full transfer | Protocolo extendido ou chunk via PKT_OTA_BLOCK? |
| 2 | Gateway timestamp sem NTP | Atual: bridge.py envia SETTIME. OK para produção? |
| 3 | node/src/neighbor_table.h era skeleton | Removido para .delete — substituído por mesh.cpp |
