
# Aguada — Telemetria de Reservatórios (ESP-NOW + Home Assistant)

Sistema de telemetria de nível/volume de reservatórios com:

- nodes ESP32-C3 (HC-SR04)
- gateway ESP32-S3 **ou ESP32 clássico** (ESP-NOW → USB serial)
- `tools/bridge.py` (cálculo + MQTT + MQTT Discovery)
- Home Assistant (dashboard, templates, automações)

## Arquitetura

`Node(s) ESP32-C3` → `Gateway ESP32-S3/ESP32` → `bridge.py` → `MQTT` → `Home Assistant`

## Build rápido

- Node:
	- `cd firmware/node && pio run`
- Gateway:
	- `cd firmware/gateway && pio run -e gateway-c3` (ESP32-C3)
	- `cd firmware/gateway && pio run -e gateway-s3` (ESP32-S3)
	- `cd firmware/gateway && pio run -e gateway-esp32-usb` (ESP32 clássico)

Upload (exemplo):
	- `cd firmware/gateway && pio run -e gateway-esp32-usb -t upload --upload-port /dev/ttyACM1`

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
