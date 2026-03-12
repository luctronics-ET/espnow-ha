# 🔌 Guia de Conexão: ESP32 + ENC28J60

## 📦 Material Necessário

- 1x ESP32 DevKit V1 (38 pinos)
- 1x Módulo ENC28J60 (SPI Ethernet)
- 7x Jumpers fêmea-fêmea
- 1x Cabo Ethernet RJ45
- 1x Fonte 5V micro-USB
- 1x Protoboard (opcional, para organização)

---

## 🎨 Pinout ENC28J60

```
┌─────────────────┐
│    ENC28J60     │
├─────────────────┤
│ • VCC  (3.3V)   │  ← Alimentação 3.3V
│ • GND           │  ← Terra
│ • SI   (MOSI)   │  ← Master Out Slave In
│ • SO   (MISO)   │  ← Master In Slave Out
│ • SCK  (Clock)  │  ← Clock SPI
│ • CS   (Select) │  ← Chip Select
│ • INT  (IRQ)    │  ← Interrupção (opcional)
│ • RST  (Reset)  │  ← Reset (opcional)
│ • CLK  (Out)    │  ← Clock Out (não usado)
└─────────────────┘
         │
         └──── RJ45 Ethernet
```

---

## 🔗 Conexões ESP32 → ENC28J60

### Tabela de Conexões

| ESP32 | Pino | ENC28J60 | Descrição |
|-------|------|----------|-----------|
| **GPIO23** | D23 | **SI (MOSI)** | Dados ESP32 → ENC |
| **GPIO19** | D19 | **SO (MISO)** | Dados ENC → ESP32 |
| **GPIO18** | D18 | **SCK** | Clock SPI |
| **GPIO5** | D5 | **CS** | Chip Select |
| **GPIO4** | D4 | **INT** | Interrupção (opcional*) |
| **3.3V** | 3V3 | **VCC** | Alimentação** |
| **GND** | GND | **GND** | Terra |

\* **INT (GPIO4):** Opcional. Melhora performance mas funciona sem.\
** **VCC:** Verificar voltagem do seu módulo (veja seção "Importante").

---

## 🎯 Diagrama de Ligação

```
ESP32 DevKit V1                     ENC28J60
┌─────────────┐                    ┌──────────┐
│             │                    │          │
│  3.3V ──────┼────────────────────┤ VCC      │
│  GND  ──────┼────────────────────┤ GND      │
│             │                    │          │
│  D23  ──────┼────────────────────┤ SI       │
│  D19  ──────┼────────────────────┤ SO       │
│  D18  ──────┼────────────────────┤ SCK      │
│  D5   ──────┼────────────────────┤ CS       │
│  D4   ──────┼────────────────────┤ INT      │
│             │                    │          │
├─────────────┤                    └──────────┘
│   USB       │                         │
│   Power     │                         │
└─────────────┘                    ──RJ45──
                                  Ethernet Cable
```

---

## ⚠️ IMPORTANTE - Alimentação

### Verificar Voltagem do Módulo

Existem 2 tipos de módulos ENC28J60:

#### Tipo 1: Módulo 3.3V PURO (mais comum)
```
┌─────────────┐
│ ENC28J60    │
│ SEM         │  ← Não tem chip regulador visível
│ REGULADOR   │  ← Conectar em 3.3V
└─────────────┘
```

**✅ Conectar VCC em 3.3V do ESP32**

---

#### Tipo 2: Módulo com Regulador 3.3V (menos comum)
```
┌─────────────┐
│ ENC28J60    │
│ AMS1117     │  ← Chip regulador visível
│ ou similar  │  ← Aceita 5V no VCC
└─────────────┘
```

**✅ Pode conectar VCC em 5V (VIN) do ESP32**

---

### Como Identificar

1. **Olhar o módulo:**
   - Tem chip regulador "AMS1117" ou "1117"? → Aceita 5V
   - Sem regulador visível? → Apenas 3.3V

2. **Ler o datasheet** do vendedor

3. **Usar multímetro:**
   - Medir voltagem no pino VCC do módulo
   - Se for chip ENC28J60 direto: 3.3V
   - Se tiver regulador antes: 5V

---

## 🛠️ Passo a Passo da Montagem

### 1. Desligar Tudo
- ESP32 **DESCONECTADO da USB**
- Sem alimentação

### 2. Conectar Alimentação
```
ESP32 3.3V  →  ENC28J60 VCC  (vermelho)
ESP32 GND   →  ENC28J60 GND  (preto)
```

### 3. Conectar SPI
```
ESP32 GPIO23  →  ENC28J60 SI/MOSI  (azul)
ESP32 GPIO19  →  ENC28J60 SO/MISO  (amarelo)
ESP32 GPIO18  →  ENC28J60 SCK     (verde)
ESP32 GPIO5   →  ENC28J60 CS      (laranja)
```

### 4. Conectar Interrupção (opcional)
```
ESP32 GPIO4  →  ENC28J60 INT  (roxo)
```

### 5. Verificar Conexões
- ✅ VCC em 3.3V (ou 5V se tiver regulador)
- ✅ GND conectado
- ✅ Jumpers bem encaixados
- ✅ Sem curtos-circuitos visíveis

### 6. Conectar Ethernet
- Plugar cabo RJ45 no módulo
- Conectar outra ponta no roteador/switch

### 7. Alimentar ESP32
- Conectar USB ao computador
- LED do encoder deve acender

---

## 🧪 Teste Básico

### Gravar Firmware de Teste

```bash
cd /home/luc/Desktop/aguada-main_nano/firmware/gateway_ethernet
idf.py set-target esp32
idf.py build
idf.py -p /dev/ttyUSB0 flash monitor
```

### Saída Esperada

```
I (1234) GTW_ETH: Inicializando Ethernet ENC28J60...
I (1245) eth: ENC28J60 driver installed
I (1256) eth: Ethernet started
I (3456) GTW_ETH: Ethernet conectado
I (4567) GTW_ETH: Ethernet obteve IP: 192.168.0.XXX
I (4568) GTW_ETH: Gateway: 192.168.0.1
I (4569) GTW_ETH: Netmask: 255.255.255.0
```

---

## 🐛 Troubleshooting

### Problema 1: "ENC28J60 not found"

**Causa:** Módulo não detectado

**Verificar:**
1. ✅ VCC e GND conectados?
2. ✅ Voltagem correta (3.3V vs 5V)?
3. ✅ Jumpers bem encaixados?
4. ✅ Módulo não está queimado?

**Teste:**
```bash
# Verificar voltagem com multímetro
# VCC do ENC28J60 deve ter 3.3V
```

---

### Problema 2: "Ethernet not started"

**Causa:** Erro de inicialização SPI

**Verificar:**
1. ✅ GPIO23 → SI
2. ✅ GPIO19 → SO
3. ✅ GPIO18 → SCK
4. ✅ GPIO5 → CS

**Teste:**
```bash
# Executar exemplo básico do ESP-IDF
cd $IDF_PATH/examples/ethernet/enc28j60
# Editar GPIOs se necessário
idf.py build flash monitor
```

---

### Problema 3: "Ethernet connected but no IP"

**Causa:** DHCP não funcionou

**Verificar:**
1. ✅ Cabo Ethernet conectado?
2. ✅ Roteador DHCP habilitado?
3. ✅ LED do módulo aceso?

**Teste manual:**
```c
// Configurar IP estático (para debug)
esp_netif_ip_info_t ip_info;
IP4_ADDR(&ip_info.ip, 192, 168, 0, 200);
IP4_ADDR(&ip_info.gw, 192, 168, 0, 1);
IP4_ADDR(&ip_info.netmask, 255, 255, 255, 0);
esp_netif_dhcpc_stop(eth_netif);
esp_netif_set_ip_info(eth_netif, &ip_info);
```

---

### Problema 4: Módulo Queima

**Causas comuns:**
- ❌ Conectou 5V em módulo 3.3V puro
- ❌ Curto-circuito durante montagem
- ❌ Módulo defeituoso de fábrica

**Prevenção:**
- ✅ Sempre desligar antes de conectar
- ✅ Verificar voltagem ANTES de ligar
- ✅ Usar protoboard para evitar curtos
- ✅ Comprar de fornecedor confiável

---

## 💡 Dicas de Instalação

### 1. Use Protoboard
- Facilita organização
- Evita jumpers soltos
- Permite testar antes de soldar

### 2. Identifique os Jumpers
- Use cores consistentes:
  - Vermelho: VCC
  - Preto: GND
  - Azul/Amarelo/Verde: Dados
  - Laranja/Roxo: Controle

### 3. Documente sua Montagem
- Tire foto do circuito funcionando
- Anote os GPIOs usados
- Guarde para referência futura

### 4. Fixação Permanente
Para instalação definitiva:
- Soldar conexões em PCB perfurada
- Ou usar shield customizado
- Proteger com caixa plástica

---

## 📸 Fotos de Referência

### Módulo ENC28J60 - Frente
```
           ┌───────────────┐
           │   █ █ █ █     │  ← LEDs
           │               │
           │  [ENC28J60]   │  ← Chip principal
           │               │
           │ ┌─────────┐   │  ← Cristal
           │ │  25MHz  │   │
           │ └─────────┘   │
           └───────────────┘
                  ││
                  ││ ← Pinos SPI
                  ││
```

### Módulo ENC28J60 - Verso
```
           ┌───────────────┐
           │               │
           │  [Transformers]│  ← Ethernet
           │               │
           │    ┌RJ45┐     │  ← Conector
           └────┴────┴─────┘
```

---

## 🔬 Testes Avançados

### Teste 1: Ping
```bash
# No ESP32, após obter IP
# Pingar gateway
ping 192.168.0.1
```

### Teste 2: HTTP Request
```bash
# Fazer requisição HTTP simples
curl http://192.168.0.137/aguada/backend/api/status.php
```

### Teste 3: Velocidade
```bash
# Testar taxa de transferência
iperf3 -c 192.168.0.137 -t 10
# Esperado: ~8-10 Mbps (ENC28J60 é 10BASE-T)
```

---

## 📊 Especificações ENC28J60

| Característica | Valor |
|----------------|-------|
| **Interface** | SPI (até 20 MHz) |
| **Velocidade Ethernet** | 10 Mbps (10BASE-T) |
| **Voltagem** | 3.3V (ou 5V com regulador) |
| **Consumo** | ~160 mA (pico), ~120 mA (típico) |
| **Buffer** | 8 KB RAM interna |
| **PHY** | Integrado |
| **Custo** | R$15-25 |

---

## ✅ Checklist Final

Antes de ligar:
- [ ] VCC conectado corretamente (3.3V ou 5V)
- [ ] GND conectado
- [ ] GPIO23 → SI (MOSI)
- [ ] GPIO19 → SO (MISO)
- [ ] GPIO18 → SCK
- [ ] GPIO5 → CS
- [ ] GPIO4 → INT (opcional)
- [ ] Cabo Ethernet conectado
- [ ] Sem curtos-circuitos visíveis
- [ ] Firmware compilado e pronto
- [ ] Porta USB identificada

Após ligar:
- [ ] LED do módulo aceso
- [ ] ESP32 inicia sem erros
- [ ] ENC28J60 detectado
- [ ] Ethernet conecta
- [ ] IP obtido via DHCP
- [ ] Ping ao gateway funciona
- [ ] HTTP POST ao backend OK

---

## 🎓 Recursos Adicionais

### Datasheets
- [ENC28J60](http://ww1.microchip.com/downloads/en/DeviceDoc/39662e.pdf)
- [ESP32](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf)

### Tutoriais ESP-IDF
```bash
$IDF_PATH/examples/ethernet/enc28j60/
```

### Bibliotecas Alternativas
- Arduino: UIPEthernet, EthernetENC
- MicroPython: uecc (menos comum)

---

## 📞 Suporte

Se encontrar problemas:

1. **Verificar documentação:** `docs/OTA_E_ETHERNET_GUIA.md`
2. **Testar exemplo ESP-IDF:** `$IDF_PATH/examples/ethernet/enc28j60/`
3. **Verificar logs:** `idf.py monitor`
4. **Consultar comunidade:** ESP32.com, Reddit /r/esp32

---

**Guia desenvolvido para o Projeto Aguada V2.3**  
**Sistema de Monitoramento de Nível de Água**

