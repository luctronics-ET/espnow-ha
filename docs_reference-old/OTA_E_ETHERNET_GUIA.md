# 🚀 Atualização OTA e Gateway Ethernet - Aguada V2.3

**Data:** 02/03/2026  
**Versão:** 2.3.0

## 📋 Índice

1. [Firmware OTA para Nodes](#firmware-ota)
2. [Gateway com Ethernet ENC28J60](#gateway-ethernet)
3. [Comparação WiFi vs Ethernet](#comparacao)
4. [Instalação e Configuração](#instalacao)
5. [Atualização Remota (OTA)](#ota-process)

---

## 🔄 Firmware OTA para Nodes {#firmware-ota}

### O que é OTA?

**OTA (Over-The-Air)** permite atualizar o firmware dos nodes remotamente, sem necessidade de conexão física USB. Ideal para nodes instalados em locais de difícil acesso.

### Características

- ✅ Atualização via HTTP/HTTPS
- ✅ Particionamento dual (ota_0 e ota_1)
- ✅ Rollback automático em caso de falha
- ✅ Access Point próprio para configuração
- ✅ Mantém todas as funcionalidades do node_universal
- ✅ LED indica status da atualização

### Estrutura de Partições

```
┌─────────────┬──────────┬────────────┬──────────┐
│   nvs       │ otadata  │   ota_0    │  ota_1   │
│  16KB       │   8KB    │  1.6MB     │  1.6MB   │
└─────────────┴──────────┴────────────┴──────────┘
    0x9000      0xD000     0x10000     0x1B0000
```

- **nvs**: Armazena configurações
- **otadata**: Controla qual partição está ativa
- **ota_0** e **ota_1**: Alternam a cada atualização

### Como Funciona

1. Node cria Access Point (ex: `Aguada-Node-6B7758`)
2. Cliente conecta ao AP (senha: `aguada2025`)
3. Envia comando de atualização com URL do firmware
4. Node baixa firmware novo para partição inativa
5. Valida e reinicia na nova versão
6. Se falhar, faz rollback automático

### Arquivos

```
node_universal_ota/
├── CMakeLists.txt
├── partitions.csv              # Tabela de partições OTA
├── sdkconfig.defaults          # Configurações ESP-IDF
└── main/
    ├── CMakeLists.txt
    └── main.c                  # Firmware com OTA
```

---

## 🌐 Gateway com Ethernet ENC28J60 {#gateway-ethernet}

### Por que usar Ethernet?

**Vantagens:**
- ✅ **Sem dependência de WiFi** - mais confiável
- ✅ **Conexão cabeada** - sem interferência
- ✅ **Menor consumo** - WiFi desligado (apenas para ESP-NOW)
- ✅ **Mais estável** - ideal para ambientes industriais
- ✅ **Custo baixo** - módulo ENC28J60: ~R$15-25

**Desvantagens:**
- ❌ Necessita cabo ethernet
- ❌ Velocidade limitada (10 Mbps) - suficiente para este projeto

### Módulo ENC28J60

<img src="https://i.imgur.com/ENC28J60.jpg" width="300">

**Especificações:**
- Interface: SPI
- Velocidade: 10 Mbps
- Voltagem: 3.3V
- Consumo: ~160mA (pico)
- Custo: R$15-25

### Pinout ESP32 + ENC28J60

```
ESP32 DevKit V1          ENC28J60
┌──────────────┐        ┌──────────┐
│              │        │          │
│  GPIO23 ─────┼────────┤ SI (MOSI)│
│  GPIO19 ─────┼────────┤ SO (MISO)│
│  GPIO18 ─────┼────────┤ SCK      │
│  GPIO5  ─────┼────────┤ CS       │
│  GPIO4  ─────┼────────┤ INT      │
│  3.3V   ─────┼────────┤ VCC      │
│  GND    ─────┼────────┤ GND      │
│              │        │          │
└──────────────┘        └──────────┘
                             │
                             └─── RJ45 Ethernet
```

**Notas:**
- ⚠️ **Usar 3.3V** (não 5V!)
- 💡 INT (GPIO4) é opcional - pode deixar desconectado
- 💡 Alguns módulos tem regulador 3.3V interno (aceita 5V no VCC)

### Funcionamento

1. **ESP-NOW** recebe dados dos nodes (via WiFi, canal 11)
2. **WiFi** é usado APENAS para ESP-NOW, não para internet
3. **Ethernet** envia dados ao servidor via cabo
4. **Backend** recebe via HTTP POST

```
     Nodes                Gateway              Servidor
┌──────────┐          ┌──────────┐          ┌──────────┐
│ ESP32-C3 │          │  ESP32   │          │  Backend │
│          │  ESP-NOW │   +      │ Ethernet │   PHP    │
│  HC-SR04 ├─────────►│ ENC28J60 ├─────────►│   API    │
│          │  Wireless│          │  Wired   │          │
└──────────┘          └──────────┘          └──────────┘
```

### Arquivos

```
gateway_ethernet/
├── CMakeLists.txt
├── sdkconfig.defaults          # Habilita driver ENC28J60
└── main/
    ├── CMakeLists.txt
    └── main.c                  # Gateway Ethernet
```

---

## ⚖️ Comparação: WiFi vs Ethernet {#comparacao}

### Gateway WiFi (Atual)

| Aspecto | Avaliação |
|---------|-----------|
| **Instalação** | ⭐⭐⭐⭐⭐ Simples, sem fios |
| **Mobilidade** | ⭐⭐⭐⭐⭐ Pode mover livremente |
| **Confiabilidade** | ⭐⭐⭐ Depende do sinal WiFi |
| **Latência** | ⭐⭐⭐⭐ ~50-100ms |
| **Consumo** | ⭐⭐⭐ ~150-200mA |
| **Custo** | ⭐⭐⭐⭐⭐ Só ESP32 (~R$35) |
| **Complexidade** | ⭐⭐⭐⭐⭐ Código simples |

**Quando usar:**
- 📱 Servidor tem WiFi disponível
- 🏠 Ambiente residencial/escritório
- 🔄 Gateway pode ser reposicionado

### Gateway Ethernet (Novo)

| Aspecto | Avaliação |
|---------|-----------|
| **Instalação** | ⭐⭐⭐ Necessita cabo ethernet |
| **Mobilidade** | ⭐⭐ Limitado pelo cabo |
| **Confiabilidade** | ⭐⭐⭐⭐⭐ Muito estável |
| **Latência** | ⭐⭐⭐⭐⭐ ~10-20ms |
| **Consumo** | ⭐⭐⭐⭐ ~120-160mA (WiFi desligado para internet) |
| **Custo** | ⭐⭐⭐⭐ ESP32 + ENC28J60 (~R$50-60) |
| **Complexidade** | ⭐⭐⭐⭐ Código moderado |

**Quando usar:**
- 🏭 Ambiente industrial
- 🔒 Rede sem WiFi disponível
- 📡 Interferência WiFi alta
- 💪 Necessita máxima estabilidade
- 🖥️ Servidor próximo (cabo ethernet alcança)

### Arduino Nano + ENC28J60 via Serial (Alternativa)

**NÃO RECOMENDADO** para este projeto:

| Aspecto | Avaliação |
|---------|-----------|
| **Custo** | ⭐⭐ Mais caro (ESP32 + Nano + ENC) |
| **Complexidade** | ⭐⭐ Muito complexo (2 MCUs) |
| **Confiabilidade** | ⭐⭐⭐ Serial pode falhar |
| **Latência** | ⭐⭐⭐ Adiciona overhead serial |
| **Manutenção** | ⭐⭐ Mais componentes = mais falhas |

**Por que não usar:**
1. ESP32 sozinho é capaz de ESP-NOW + Ethernet
2. Adiciona ponto de falha extra (comunicação serial)
3. Mais caro e complexo
4. Ocupa mais espaço

---

## 🛠️ Instalação e Configuração {#instalacao}

### Pré-requisitos

```bash
# ESP-IDF já instalado
. $HOME/esp/esp-idf/export.sh

# Verificar
idf.py --version
```

### 1. Compilar Node OTA

```bash
cd /home/luc/Desktop/aguada-main_nano/firmware/node_universal_ota

# Configurar target
idf.py set-target esp32c3

# Compilar
idf.py build

# Gravar via USB (primeira vez)
idf.py -p /dev/ttyUSB0 flash monitor
```

### 2. Compilar Gateway Ethernet

```bash
cd /home/luc/Desktop/aguada-main_nano/firmware/gateway_ethernet

# Configurar target
idf.py set-target esp32

# Compilar
idf.py build

# Gravar
idf.py -p /dev/ttyUSB0 flash monitor
```

### 3. Hardware - Conectar ENC28J60

**Material necessário:**
- 1x ESP32 DevKit V1
- 1x Módulo ENC28J60
- 7x Jumpers fêmea-fêmea
- 1x Cabo ethernet
- 1x Fonte 5V micro-USB

**Conexões:**

| ESP32 | ENC28J60 | Cor sugerida |
|-------|----------|--------------|
| GPIO23 | SI (MOSI) | Azul |
| GPIO19 | SO (MISO) | Amarelo |
| GPIO18 | SCK | Verde |
| GPIO5 | CS | Laranja |
| GPIO4 | INT | Roxo (opcional) |
| 3.3V | VCC | Vermelho |
| GND | GND | Preto |

**⚠️ ATENÇÃO:**
- Verificar se o módulo é 3.3V ou tem regulador interno
- Se tiver regulador, pode usar 5V do ESP32
- Checar datasheet do seu módulo!

### 4. Configurar Servidor Backend

**Atualizar IP do servidor** no código (se necessário):

```bash
# Editar gateway_ethernet/main/main.c
nano gateway_ethernet/main/main.c

# Localizar linha:
#define BACKEND_URL "http://192.168.0.137/aguada/backend/api/api_gateway_v3.php"

# Alterar IP para seu servidor
# Salvar e recompilar
```

---

## 📡 Processo de Atualização OTA {#ota-process}

### Preparar Firmware Novo

1. **Modificar código** do node_universal_ota
2. **Incrementar versão** em `FIRMWARE_VERSION`
3. **Compilar:**

```bash
cd node_universal_ota
idf.py build
```

4. **Copiar binário** para servidor web:

```bash
# Binário gerado em:
build/node_universal_ota.bin

# Copiar para servidor:
scp build/node_universal_ota.bin usuario@192.168.0.137:/var/www/html/aguada/ota/firmware.bin
```

### Atualizar Node Remotamente

#### Método 1: Via WiFi (do seu PC)

```bash
# 1. Conectar ao AP do node
# SSID: Aguada-Node-XXXXXX
# Senha: aguada2025

# 2. Enviar comando de atualização
curl -X POST http://192.168.4.1/ota \
  -d "url=http://192.168.0.137/aguada/ota/firmware.bin"

# 3. Aguardar conclusão (LED piscará rapidamente)
# 4. Node reinicia automaticamente
```

#### Método 2: Trigger via Código

Adicionar no `main.c` do node:

```c
// No app_main(), após ESP-NOW inicializar:

// Verificar se há atualização disponível
if (check_for_update()) {
    start_ota_update("http://192.168.0.137/aguada/ota/firmware.bin");
}
```

#### Método 3: Via Gateway (futuro)

Gateway pode comandar nodes para atualizar (requer implementação adicional).

### Indicações LED durante OTA

| Padrão LED | Significado |
|------------|-------------|
| 10 piscadas rápidas | OTA iniciado |
| Pisca continuamente | Download em progresso |
| 3 piscadas longas | OTA concluído, reiniciando |
| 3 piscadas curtas | Erro na atualização |

### Rollback Automático

Se o firmware novo tiver problemas:

1. Node inicia com firmware novo
2. **Watchdog** detecta travamento ou falha
3. Após 3 tentativas, faz **rollback** automático
4. Retorna ao firmware anterior (estável)

Para forçar validação do firmware novo:

```c
// Adicionar no app_main() após inicialização bem-sucedida:
const esp_partition_t* partition = esp_ota_get_running_partition();
esp_ota_img_states_t ota_state;

if (esp_ota_get_state_partition(partition, &ota_state) == ESP_OK) {
    if (ota_state == ESP_OTA_IMG_PENDING_VERIFY) {
        // Firmware funcionando OK, validar
        esp_ota_mark_app_valid_cancel_rollback();
        ESP_LOGI(TAG, "Firmware validado!");
    }
}
```

---

## 🧪 Testando o Sistema

### Teste 1: Node OTA

```bash
# Terminal 1: Monitor node
cd node_universal_ota
idf.py -p /dev/ttyUSB0 monitor

# Verificar:
# ✅ MAC address exibido
# ✅ Access Point criado (Aguada-Node-XXXXXX)
# ✅ ESP-NOW inicializado no canal 11
# ✅ Medições enviadas a cada 30s
```

### Teste 2: Gateway Ethernet

```bash
# Terminal 1: Monitor gateway
cd gateway_ethernet
idf.py -p /dev/ttyUSB1 monitor

# Verificar:
# ✅ ENC28J60 inicializado
# ✅ Ethernet conectado
# ✅ IP obtido via DHCP
# ✅ ESP-NOW inicializado no canal 11
# ✅ Pacotes recebidos e filtrados
# ✅ HTTP POST enviado ao backend
```

### Teste 3: Comunicação End-to-End

```bash
# 1. Ligar node e gateway
# 2. Aguardar 30s (intervalo de medição)
# 3. Verificar logs do gateway:
#    - Pacote recebido
#    - Filtro aplicado
#    - HTTP POST enviado
# 4. Verificar banco de dados:
mysql -u root -p aguada
SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
```

---

## 🐛 Troubleshooting

### Problema: Node não conecta ao Gateway

**Causa:** Canal WiFi diferente

**Solução:**
```c
// Em ambos node e gateway, garantir:
#define WIFI_CHANNEL 11  // Mesmo canal!
```

### Problema: ENC28J60 não inicializa

**Sintomas:** `Ethernet init falhou`

**Verificar:**
1. ✅ Conexões SPI corretas
2. ✅ Voltagem 3.3V (não 5V se módulo não tem regulador)
3. ✅ Jumpers bem conectados
4. ✅ Módulo não defeituoso (testar com exemplo básico)

**Teste básico:**
```bash
cd $IDF_PATH/examples/ethernet/enc28j60
idf.py set-target esp32
# Editar GPIOs em main/ethernet_example_main.c
idf.py build flash monitor
```

### Problema: OTA falha

**Sintomas:** LED pisca 3 vezes (erro)

**Causas comuns:**
1. ❌ URL incorreta
2. ❌ Servidor web não acessível
3. ❌ Firmware binário corrompido
4. ❌ Partições mal configuradas

**Verificar:**
```bash
# 1. Testar URL manualmente
curl -I http://192.168.0.137/aguada/ota/firmware.bin

# 2. Verificar tamanho do binário (deve ser < 1.6MB)
ls -lh node_universal_ota/build/node_universal_ota.bin

# 3. Verificar partições
idf.py partition-table
```

### Problema: Gateway não envia ao backend

**Sintomas:** Pacotes recebidos mas não enviados

**Ve verificar:**
1. ✅ Ethernet tem IP válido
2. ✅ Servidor backend alcançável
3. ✅ Filtro não está descartando pacotes

**Debug:**
```bash
# No gateway, adicionar log:
ESP_LOGI(TAG, "Should send? %s", should_send_to_backend(packet) ? "YES" : "NO");

# Testar backend manualmente:
curl -X POST http://192.168.0.137/aguada/backend/api/api_gateway_v3.php \
  -H "Content-Type: application/json" \
  -d '{"mac":"20:6E:F1:6B:77:58","value_id":1,"value_data":100,"sequence":1,"rssi":-45}'
```

---

## 📊 Monitoramento

### Logs Gateway

```bash
# Acompanhar em tempo real
idf.py -p /dev/ttyUSB1 monitor

# Filtrar apenas pacotes recebidos
idf.py -p /dev/ttyUSB1 monitor | grep "Pacote recebido"

# Verificar status a cada 10s
# (implementado no código - monitor_task)
```

### Status do Sistema

Gateway imprime status a cada 10 segundos:

```
I (10000) GTW_ETH: === STATUS ===
I (10000) GTW_ETH: Ethernet: Conectado | IP: OK
I (10000) GTW_ETH: Backend: OK
I (10000) GTW_ETH: Pacotes: RX=120 TX=45 Erros=0
I (10000) GTW_ETH: =============
```

---

## 📚 Referências

### Documentação Oficial

- [ESP-IDF OTA](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/ota.html)
- [ESP-IDF Ethernet](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_eth.html)
- [ESP-NOW Protocol](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_now.html)

### Exemplos ESP-IDF

```bash
# OTA
$IDF_PATH/examples/system/ota/

# Ethernet ENC28J60
$IDF_PATH/examples/ethernet/enc28j60/

# ESP-NOW
$IDF_PATH/examples/wifi/espnow/
```

### Datasheets

- [ENC28J60](http://ww1.microchip.com/downloads/en/DeviceDoc/39662e.pdf)
- [ESP32](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)
- [ESP32-C3](https://www.espressif.com/sites/default/files/documentation/esp32-c3_datasheet_en.pdf)

---

## ✅ Checklist de Implantação

### Preparação

- [ ] ESP-IDF instalado e configurado
- [ ] Código compilado sem erros
- [ ] ENC28J60 conectado corretamente
- [ ] Servidor backend acessível
- [ ] Cabo ethernet conectado e testado

### Node OTA

- [ ] Firmware node_universal_ota compilado
- [ ] Gravado via USB com sucesso
- [ ] Access Point visível
- [ ] ESP-NOW enviando pacotes
- [ ] LED piscando em cada envio

### Gateway Ethernet

- [ ] Firmware gateway_ethernet compilado
- [ ] ENC28J60 detectado e inicializado
- [ ] IP obtido via DHCP
- [ ] ESP-NOW recebendo pacotes dos nodes
- [ ] HTTP POST chegando ao backend
- [ ] Dados sendo salvos no banco

### OTA

- [ ] Binário novo copiado para servidor web
- [ ] URL acessível via curl/browser
- [ ] Node consegue baixar firmware
- [ ] Atualização completa com sucesso
- [ ] Rollback funciona em caso de falha

---

## 🎯 Próximos Passos

### Melhorias Sugeridas

1. **Web Interface para OTA**
   - Página web no AP do node
   - Upload de firmware pelo browser
   - Status visual da atualização

2. **OTA em Massa**
   - Gateway comanda atualização de todos os nodes
   - Atualização sequencial (1 por vez)
   - Verificação de versão antes de atualizar

3. **Gateway Dual-Mode**
   - WiFi + Ethernet simultâneos
   - Failover automático
   - Prioriza Ethernet, fallback para WiFi

4. **Monitoramento Remoto**
   - Dashboard web com status dos nodes
   - Alertas de nodes offline
   - Histórico de versões de firmware

5. **Segurança**
   - HTTPS para OTA
   - Assinatura digital do firmware
   - Autenticação no backend

---

## 💡 Dicas Finais

### Performance

- ⚡ Ethernet ENC28J60 é limitado a 10 Mbps (mais que suficiente)
- ⚡ WiFi pode ter latência variável (50-100ms)
- ⚡ Ethernet tem latência consistente (~10-20ms)

### Confiabilidade

- 🛡️ Ethernet é mais estável em ambientes industriais
- 🛡️ WiFi pode sofrer interferência de outros dispositivos
- 🛡️ Ambos são adequados para este projeto

### Custo

- 💰 WiFi: ~R$35 (só ESP32)
- 💰 Ethernet: ~R$50-60 (ESP32 + ENC28J60)
- 💰 Diferença baixa para ganho em estabilidade

### Decisão

**Use WiFi se:**
- Servidor tem WiFi disponível
- Mobilidade é importante
- Custo é crítico

**Use Ethernet se:**
- Ambiente industrial/comercial
- Máxima estabilidade necessária
- Servidor próximo (cabo alcança)
- Rede WiFi congestionada/indisponível

---

**Desenvolvido para o Projeto Aguada V2**  
**Monitoramento de Nível de Água com ESP32**

