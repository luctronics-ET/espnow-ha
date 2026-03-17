
# Aguada — Telemetria de Reservatórios (ESP-NOW + Home Assistant)

Sistema de telemetria de nível/volume de reservatórios com:

- nodes ESP32-C3 (HC-SR04)
- gateway ESP32-S3 (ESP-NOW → USB serial)
- `tools/bridge.py` (cálculo + MQTT + MQTT Discovery)
- Home Assistant (dashboard, templates, automações)

## Arquitetura

`Node(s) ESP32-C3` → `Gateway ESP32-S3` → `bridge.py` → `MQTT` → `Home Assistant`

## Build rápido

- Node:
	- `cd firmware/node && pio run`
- Gateway:
	- `cd firmware/gateway && pio run`

## Bridge

Dependências:

- `pip install -r tools/requirements.txt`

Execução:

- `python tools/bridge.py --port /dev/ttyACM0 --mqtt localhost`

## Home Assistant — migração limpa (recomendado)

Para evitar entidades duplicadas ou sem dados:

1. **Use MQTT Discovery para reservatórios** (CON/CAV/CB*/CIE*), publicado pelo `bridge.py`.
2. **Mantenha manualmente apenas sensores do gateway** via:
	 - `homeassistant/mqtt_gateway_sensors.yaml`
3. No `configuration.yaml` do HA, use:
	 - `mqtt: !include aguada/mqtt_gateway_sensors.yaml`
	 - `sensor: !include aguada/statistics_sensors.yaml`
	 - `template: !include aguada/template_sensors.yaml`
	 - `automation: !include automations.yaml`

Arquivos de referência neste repositório:

- `homeassistant/configuration_snippet.yaml`
- `homeassistant/configuration_full.yaml`

## Importante

- O arquivo `homeassistant/mqtt_sensors.yaml` é **legado** e não deve ser usado junto com discovery.
- Especificação oficial: `AGUADA_SYSTEM_DOC.md`.
- Pinagem atual de Node/Relay: `PINAGEM.md`.
