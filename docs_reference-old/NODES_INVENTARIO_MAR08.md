## 1. DESCRIÇÃO RESUMIDA DO SISTEMA

### 1.1 Visão Geral

Sistema de telemetria e monitoramento hídrico baseado em ESP32 para o Centro de Mísseis e Armas Submarinas da Marinha (CMASM), localizado na Ilha do Engenho, São Gonçalo - RJ.

**Objetivo**: Monitorar em tempo real o nível de água em reservatórios e cisternas da infraestrutura predial do CMASM, permitindo:
- Controle operacional centralizado
- Detecção automática de vazamentos
- Balanço hídrico diário
- Alertas de nível crítico
- Histórico de consumo e abastecimento

# Inventário de Nodes - Aguada V2.2

Nodes x Reservatorios
  
- NODE-01 (single ultrasonic sensor)
   node_id= 01, sensor_id = 1, alias: `CON`, nome: `Castelo de Consumo`, max-vol: 80m³, max lvl: 450cm, offset: 20cm
 
- NODE-02 (single ultrasonic sensor)
   node_id= 02, sensor_id = 1, alias: `CAV`, nome: `Castelo de Incendio` - max-vol: 80m³, max lvl: 450cm, offset: 20cm 
   // implementar com nano+eth. já existente. nano envia direto ao db ou ao gateway...

 - NODE-03 (dual ultrasonic sensor) alias: `CB03`, nome: `Casa de Bombas N03`, max-vol: 80m³ (CB03.volume = CB31.volume + CB32.volume) (o volume de CB03 e a soma dos dois reservatorios)
  node_id= 03, sensor_id = 1, alias: `CB31` nome: `Casa de Bombas N3.1`, max-vol: 40m³, max lvl: 200cm, offset: 10cm 
  node_id= 03, sensor_id = 2, alias: `CB32` nome: `Casa de Bombas N3.2`, max-vol: 40m³, max lvl: 200cm, offset: 10cm 

- NODE-04 (dual ultrasonic sensor) (dois reservatorios independentes)
    node_id= 04, sensor_id = 1, alias: `CIE1`, nome: `Cisterna CIE1`, max-vol: 245m³, max lvl: 200cm, offset: 10cm 
    node_id= 04, sensor_id = 2, alias: `CIE2`, nome: `Cisterna CIE2`, max-vol: 245m³, max lvl: 200cm, offset: 10cm 

- NODE-05 (CBIF):  max-vol: 80m³ (CBIF.volume = CBIF1.volume + CBIF2.volume (manual input, no sensor now) (o volume de CBIF e a soma dos dois reservatorios)
    node_id= 05, sensor_id = 1, alias: `CBIF1`, nome: `Casa de Bombas IF.1`, max-vol: 40m³, max lvl: 200cm, offset: 10cm 
    node_id= 05, sensor_id = 2, alias: `CBIF2`, nome: `Casa de Bombas IF.2`, max-vol: 40m³, max lvl: 200cm, offset: 10cm 


 **1x ESP32-C3 Supermini**: Gateway receptor ESP-NOW → HTTP (wifi)
 
  *1x ESP32 DevKit V1**: Gateway receptor ESP-NOW → HTTP (wifi + ethernet) (implementacao futura)
 
---  

## 📋 Resumo

| Node     | Hardware | MAC Address       | 
|----------|----------|-------------------|
| NODE-001 | ESP32-C3 | 20:6E:F1:6B:77:58 | 
| NODE-002 | Nano     | AA:BB:CC:DD:EE:02 | 
| NODE-003 | ESP32-C3 | 80:F1:B2:50:2E:C4 | 
| NODE-004 | ESP32-C3 | DC:B4:D9:8B:9E:AC | 
| NODE-005 | ESP32-C3 | 24:EC:4A:12:34:56 | 

**Gateway:** ESP32 DevKit V1 - MAC `24:D7:EB:5B:2E:74` 
**Gateway:** 1x ESP32-C3 Supermini**: Gateway receptor ESP-NOW → HTTP (wifi)
---



## 🔧 Pinout

### ESP32-C3 Super Mini (Node)

**Single Sensor:**
```
GPIO1 → TRIG (HC-SR04)
GPIO0 → ECHO (HC-SR04)
GPIO8 → LED builtin
```

**Dual Sensor:**
```
GPIO1 → TRIG1 (Sensor 1)
GPIO0 → ECHO1 (Sensor 1)
GPIO3 → TRIG2 (Sensor 2)
GPIO2 → ECHO2 (Sensor 2)
GPIO8 → LED builtin



### 3.5 Balanço Hídrico (Análise Diária)

**Objetivo**: Detectar vazamentos comparando consumo real vs. esperado

#### 3.5.1 Conceitos

```
BALANÇO = VOLUME_FINAL - VOLUME_INICIAL

• BALANÇO > 0 → ENTRADA (abastecimento do reservatório)
• BALANÇO < 0 → SAÍDA (consumo de água)
```

**Exemplo NODE-01 (CON):**
```
08:00 → Volume = 60.000 L
18:00 → Volume = 45.000 L

BALANÇO = 45.000 - 60.000 = -15.000 L
→ CONSUMO = 15.000 L em 10 horas = 1.500 L/h

## RELATORIO HIDRICO DIARIO

Local               |  hora   | VOL M3
'Castelo de Consumo |  06h00' | 74 
'Castelo de Consumo |  08h00' | 72 
'Castelo de Consumo |  10h00' | 70 
'Castelo de Consumo |  13h15' | 66 
'Castelo de Consumo |  15h00' | 64 
'Castelo de Consumo |  17h00' | 62 
'Castelo de Consumo |  21h00' | 61 
'Castelo de Consumo |  06h00' | 60 
'Consumo Estimado'            | 14    

Local               | anterior (M3) | atual (M3) | BALANCO (M3) |
Castelo de Incêndio | 70           | 69        | -1
Casa de Bombas IF   | 10           | 10        | 0
Casa de Bombas nº3  | 40           | 40        | 0
Cisterna nº1        | 128          | 128       | 0
Cisterna nº2        | 136          | 136       | 0

Hidrômetro IF (HID-IF)      | 10142        | 10142     |    0          |
Hidrômetro Praia (HID-PRAIA)   | 24765        | 24765     |    0          |
Hidrômetro AV (HID-AV) | 11530        | 11535     |    5          |
Hidrômetro AV/AZ (HID-AV|AZ)  | 27694,38     | 27707,64  |  13,26        |


## HIDROMETROS

hidrometro   |  anterior  |  atual  |  delta | status |
HID-IF
HID-PRAIA
---------------------------------------------------------
		     Tubo submarino |   xx     | vazamento no tubo
-------------------------------------------------		     
hidrometro   |  anterior  |  atual  |  delta | status |
HID-AV|AZ
HID-AV
---------------------------------------------------------
HID-AZ = 	(Delta AV|AZ - delta AV)	
-------------------------------------------------		   




## NODES

## 🔧 NODE-001

**Hardware:**
- ESP32-C3 Super Mini
- 1x Sensor HC-SR04

**Firmware:** `node_universal` v2.2  
**MAC Address:** `20:6E:F1:6B:77:58`  
**Porta COM:** COM5

**Configuração:**
```c
#define TRIG_GPIO   GPIO_NUM_1
#define ECHO_GPIO   GPIO_NUM_0
#define LED_GPIO    GPIO_NUM_8  // Built-in LED (active-low)
```

**Transmissão:**
- Intervalo: 30 segundos
- sensor_id: 1
- Canal ESP-NOW: 1

**Última Gravação:** 03/01/2026 10:XX

---

## 🔧 NODE-002

**Hardware:**
- Arduino Nano ATmega328P (Old Bootloader)
- ENC28J60 Ethernet Module
- 1x Sensor HC-SR04

**Firmware:** `node_nano_eth_ultra_01` v2.2  
**MAC Address (Artificial):** `AA:BB:CC:DD:EE:02`  
**Porta COM:** COM9 (57600 baud - old bootloader)

**Rede:**
- IP Estático: 192.168.1.202
- Gateway: 192.168.1.1
- Servidor: 192.168.1.102 (XAMPP)

**Configuração:**
```cpp
#define TRIGGER_PIN 6
#define ECHO_PIN 5
#define LED_PIN 13  // Built-in LED

// Rede
IPAddress ip(192, 168, 1, 202);
IPAddress server(192, 168, 1, 102);
```

**Transmissão:**
- Protocolo: HTTP POST direto (não usa ESP-NOW)
- API: `http://192.168.1.102/aguada/backend/api/api_gateway_v3.php`
- Intervalo: 30 segundos
- sensor_id: 1
- MAC artificial registrado em `nodes_autorizados`

**Compilação:**
```powershell
cd c:\Users\luc10\aguada\firmware\' node-02-cav'
pio run --target upload --upload-port COM9
```

**Última Gravação:** 03/01/2026 11:00

**Observações:**
- Único node que usa Ethernet ao invés de ESP-NOW
- Watchdog desabilitado para debug
- MAC artificial (AA:BB:CC:DD:EE:02) para compatibilidade com protocolo V2.2
- Envia dados diretamente ao backend (bypass do gateway)

---

## 🔧 NODE-003

**Hardware:**
- ESP32-C3 Super Mini
- 1x Sensor HC-SR04

**Firmware:** `node_universal` v2.2  
**MAC Address:** `80:F1:B2:50:2E:C4`  
**Porta COM:** COM6

**Configuração:**
```c
#define TRIG_GPIO   GPIO_NUM_1
#define ECHO_GPIO   GPIO_NUM_0
#define LED_GPIO    GPIO_NUM_8  // Built-in LED (active-low)
```

**Transmissão:**
- Intervalo: 30 segundos
- sensor_id: 1
- Canal ESP-NOW: 1

**Última Gravação:** 03/01/2026 10:13

---

## 🔧 NODE-004 (Dual Sensor)

**Hardware:**
- ESP32-C3 Super Mini
- 2x Sensores HC-SR04

**Firmware:** `node_universal_dual` v2.2  
**MAC Address:** `DC:B4:D9:8B:9E:AC`  
**Porta COM:** COM8

**Configuração:**
```c
// Sensor 1
#define TRIG1_GPIO   GPIO_NUM_1
#define ECHO1_GPIO   GPIO_NUM_0

// Sensor 2
#define TRIG2_GPIO   GPIO_NUM_3
#define ECHO2_GPIO   GPIO_NUM_2

#define LED_GPIO     GPIO_NUM_8  // Built-in LED (active-low)
```

**Transmissão:**
- Intervalo: 30 segundos
- **sensor_id: 1** (Sensor 1 em GPIO0/1)
- **sensor_id: 2** (Sensor 2 em GPIO2/3, 100ms depois)
- Canal ESP-NOW: 1

**⚠️ Importante:** Envia 2 pacotes separados a cada ciclo de 30 segundos.

**Última Gravação:** 03/01/2026 10:21

---

## 🔧 NODE-005 (Dual Sensor)

**Hardware:**
- ESP32-C3 Super Mini
- 2x Sensores HC-SR04

**Firmware:** `node-05-dual` v2.2  
**MAC Address:** `24:EC:4A:12:34:56`  
**Porta COM:** COM7

**Configuração:**
```c
// Sensor 1
#define TRIG1_GPIO   GPIO_NUM_1
#define ECHO1_GPIO   GPIO_NUM_0

// Sensor 2
#define TRIG2_GPIO   GPIO_NUM_3
#define ECHO2_GPIO   GPIO_NUM_2

#define LED_GPIO     GPIO_NUM_8  // Built-in LED (active-low)
```

**Transmissão:**
- Intervalo: 30 segundos
- **sensor_id: 1** (Sensor 1 em GPIO0/1)
- **sensor_id: 2** (Sensor 2 em GPIO2/3, 100ms depois)
- Canal ESP-NOW: 1

**⚠️ Importante:** Envia 2 pacotes separados a cada ciclo de 30 segundos.

**Status:** 🔨 Firmware criado, aguardando primeira gravação

**Para compilar e gravar:**
```powershell
# Abrir "ESP-IDF PowerShell"
cd C:\Users\luc10\aguada\firmware\node-05-dual
.\build_and_flash.ps1
```

---

## 🌐 Gateway

**Hardware:**
- ESP32 DevKit V1 (ESP32 Dual Core)
- WiFi + ESP-NOW simultâneos

**Firmware:** `gateway_wifi` v2.2  
**MAC Address:** `24:D7:EB:5B:2E:74`  
**Porta COM:** COM4

**Configuração:**
```c
#define ESPNOW_CHANNEL  1
#define WIFI_SSID       "esp32"
#define WIFI_PASS       ""
#define BACKEND_URL     "http://192.168.1.102/aguada/backend/api/api_gateway_v3.php"
```

**Rede WiFi:**
- SSID: `esp32`
- Canal: 1 (fixo, para ESP-NOW)
- IP: DHCP (tipicamente 192.168.1.100)

**Função:**
1. Recebe pacotes ESP-NOW (13 bytes) no canal 1
2. Valida tamanho e estrutura
3. Preenche campo RSSI
4. Converte para JSON
5. Envia via HTTP POST para backend

**Última Gravação:** 03/01/2026 09:26

---

## 📦 Compilação

### Node Universal (NODE-001, NODE-002, NODE-003)

```bash
cd /c/Users/luc10/aguada/firmware/node_universal
C:/Espressif/python_env/idf6.0_py3.11_env/Scripts/python.exe \
  C:/Espressif/frameworks/esp-idf-v6.0/tools/idf.py build
```

**Binários gerados:**
- `build/bootloader/bootloader.bin`
- `build/partition_table/partition-table.bin`
- `build/node_universal.bin`

**Tamanho:** ~777 KB

### Node Universal Dual (NODE-004)

```bash
cd /c/Users/luc10/aguada/firmware/node_universal_dual
C:/Espressif/python_env/idf6.0_py3.11_env/Scripts/python.exe \
  C:/Espressif/frameworks/esp-idf-v6.0/tools/idf.py build
```

**Binários gerados:**
- `build/bootloader/bootloader.bin`
- `build/partition_table/partition-table.bin`
- `build/node_universal.bin`

**Tamanho:** ~778 KB

### Gateway WiFi

```bash
cd /c/Users/luc10/aguada/firmware/gateway_wifi
C:/Espressif/python_env/idf6.0_py3.11_env/Scripts/python.exe \
  C:/Espressif/frameworks/esp-idf-v6.0/tools/idf.py build
```

**Binários gerados:**
- `build/bootloader/bootloader.bin`
- `build/partition_table/partition-table.bin`
- `build/gateway_wifi.bin`

**Tamanho:** ~818 KB

---

## 🔌 Gravação (Flash)

### Comando Universal

```powershell
C:\Espressif\python_env\idf6.0_py3.11_env\Scripts\python.exe -m esptool `
  --chip esp32c3 `
  -p COMX `
  -b 460800 `
  --before default-reset `
  --after hard-reset `
  write-flash `
  --flash-mode dio `
  --flash-size 4MB `
  --flash-freq 80m `
  0x0 build\bootloader\bootloader.bin `
  0x8000 build\partition_table\partition-table.bin `
  0x10000 build\node_universal.bin
```

**Substitua:**
- `COMX` pela porta correta (COM5, COM6, COM7, COM8)
- `node_universal.bin` por `gateway_wifi.bin` se for o gateway

### Sequência de Gravação

1. **NODE-001 (COM5):**
   ```bash
   cd firmware/node_universal
   # Flash com comando acima usando -p COM5
   ```

2. **NODE-002 (COM7):**
   ```bash
   cd firmware/node_universal
   # Flash com comando acima usando -p COM7
   ```

3. **NODE-003 (COM6):**
   ```bash
   cd firmware/node_universal
   # Flash com comando acima usando -p COM6
   ```

4. **NODE-004 (COM8):**
   ```bash
   cd firmware/node_universal_dual
   # Flash com comando acima usando -p COM8
   ```

5. **Gateway (COM4):**
   ```bash
   cd firmware/gateway_wifi
   # Flash com comando acima usando -p COM4 e gateway_wifi.bin
   ```

---

## 🗄️ Registro no Banco de Dados

Todos os nodes devem estar registrados na tabela `nodes_autorizados`:

```sql
INSERT INTO nodes_autorizados (mac_address) VALUES 
('20:6E:F1:6B:77:58'),  -- NODE-001
('DC:06:75:67:6A:CC'),  -- NODE-002
('80:F1:B2:50:2E:C4'),  -- NODE-003
('DC:B4:D9:8B:9E:AC');  -- NODE-004
```

**Verificar registro:**
```sql
SELECT * FROM nodes_autorizados;
```

---

## 📊 Monitoramento

### Logs do Gateway

```bash
# Via ESP-IDF Monitor
C:\Espressif\python_env\idf6.0_py3.11_env\Scripts\python.exe \
  C:\Espressif\frameworks\esp-idf-v6.0\tools\idf.py -p COM4 monitor
```

**Logs esperados:**
```
I (XXX) GATEWAY: 📥 RX: MAC=20:6E:F1:6B:77:58, sensor=1, dist=96 cm, seq=42, RSSI=-58 dBm
I (XXX) GATEWAY: 📤 HTTP POST: {"mac_address":"20:6E:F1:6B:77:58","readings":[{"sensor_id":1,"distance_cm":96}],"sequence":42,"rssi":-58}
I (XXX) GATEWAY: ✅ Backend: OK (200)
```

### Logs dos Nodes

```bash
# Conecte o node via USB
C:\Espressif\python_env\idf6.0_py3.11_env\Scripts\python.exe \
  C:\Espressif\frameworks\esp-idf-v6.0\tools\idf.py -p COMX monitor
```

**Logs esperados:**
```
I (XXX) NODE: 🔧 Iniciando node universal
I (XXX) NODE: MAC: 20:6E:F1:6B:77:58
I (XXX) NODE: 📡 Medindo sensores...
I (XXX) NODE: 📏 Sensor 1: 96 cm
I (XXX) NODE: 📤 TX: sensor=1, dist=96 cm, seq=42
```

### Dashboard Web

Acesse: `http://localhost/aguada/ver_leituras_novas.php`

Mostra todas as leituras em tempo real com:
- MAC address do node
- sensor_id (1 ou 2)
- Distância em cm
- Timestamp
- RSSI

---

## 🔍 Troubleshooting

### Node não aparece no banco

1. **Verificar se MAC está autorizado:**
   ```sql
   SELECT * FROM nodes_autorizados WHERE mac_address='XX:XX:XX:XX:XX:XX';
   ```

2. **Adicionar MAC se necessário:**
   ```sql
   INSERT IGNORE INTO nodes_autorizados (mac_address) VALUES ('XX:XX:XX:XX:XX:XX');
   ```

3. **Verificar logs do gateway:**
   - Se aparecer "Pacote inválido: 12 bytes" → Node tem firmware antigo
   - Se aparecer "⚠️ Backend: status 404" → MAC não autorizado

### Leituras 65535 (0xFFFF)

- Sensor HC-SR04 desconectado ou com problema
- Verifique conexões TRIG e ECHO
- Alimentação 5V do sensor

### Gateway não recebe pacotes

- Verificar que WiFi e ESP-NOW estão no mesmo canal (1)
- Nodes devem estar ligados e transmitindo
- Distância máxima ~50m em ambiente aberto

---

## 📝 Notas de Versão

### v2.2 (03/01/2026)

**✅ Implementado:**
- Novo protocolo com `value_id` + `value_data` (13 bytes)
- Suporte a múltiplos sensores por node
- Node dual com 2 sensores HC-SR04
- API V3 com validação de MAC
- Tabelas simplificadas no banco de dados
- Todos os 4 nodes atualizados e testados

**🔧 Alterações no Firmware:**
- `sensor_packet_t`: Adicionado campo `value_id`
- Gateway valida tamanho exato de 13 bytes
- Node dual envia 2 pacotes com delay de 100ms

**📊 Alterações no Backend:**
- Nova API: `api_gateway_v3.php`
- Nova tabela: `leituras_nodes` (com sensor_id)
- Nova tabela: `nodes_autorizados` (whitelist de MACs)

**✅ Status:**
Todos os componentes testados e operacionais!
