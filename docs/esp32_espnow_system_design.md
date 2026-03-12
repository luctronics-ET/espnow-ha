# Sistema de Rede ESP32 com ESP‑NOW, Gateway USB e OTA

## Visão Geral

O objetivo do sistema é criar uma rede de sensores e atuadores baseada
em **ESP32** utilizando **ESP‑NOW** como protocolo de comunicação
principal, com:

-   Gateway USB conectado ao servidor (Home Assistant ou outro sistema)
-   Nodes ESP32 distribuídos (sensores / repetidores / atuadores)
-   Atualização remota de firmware (**OTA -- Over The Air**)
-   Auto‑configuração e auto‑descoberta de dispositivos
-   Arquitetura escalável e robusta para ambientes externos

Esse modelo elimina dependências de:

-   Wi‑Fi no campo
-   roteadores
-   DHCP
-   infraestrutura de rede adicional

------------------------------------------------------------------------

# Arquitetura do Sistema

    Home Assistant / Servidor
            │
            │ USB
            │
    Gateway ESP32‑S3
            │
         ESP‑NOW
            │
       Mesh multi‑hop
            │
    Nodes ESP32 sensores / relays

Características:

-   Gateway recebe dados e envia comandos
-   Nodes podem funcionar como **sensor ou relay**
-   Qualquer node pode virar gateway quando conectado por USB
-   Comunicação confiável em ambientes com vegetação

------------------------------------------------------------------------

# OTA -- Atualização Remota de Firmware

Após a primeira gravação por USB, os dispositivos podem ser atualizados
remotamente.

## Fluxo OTA

    Novo firmware
          ↓
    Gateway
          ↓
    ESP‑NOW mesh
          ↓
    Nodes

Isso permite:

-   adicionar funcionalidades
-   corrigir bugs
-   atualizar drivers de sensores
-   melhorar rede sem acesso físico ao node

------------------------------------------------------------------------

# Primeiro Firmware (Bootstrap)

A primeira versão gravada por USB deve conter:

-   ESP‑NOW stack
-   mesh básico
-   OTA
-   configuração BLE
-   drivers básicos
-   sistema de configuração

Estrutura sugerida:

    boot
    radio
    mesh
    ota
    config
    drivers

Depois disso o sistema evolui via OTA.

------------------------------------------------------------------------

# Estrutura de Partições OTA

ESP32 precisa de duas partições de firmware.

    nvs
    otadata
    app0
    app1
    spiffs

Funcionamento:

    executando app0
    ↓
    grava app1
    ↓
    reinicia
    ↓
    executa app1

Se falhar:

    rollback automático

------------------------------------------------------------------------

# Segurança OTA

Recomendado implementar:

-   CRC
-   SHA256
-   verificação de tamanho
-   rollback automático

Isso evita firmware corrompido.

------------------------------------------------------------------------

# Tempo de Atualização OTA

Exemplo:

Firmware: 800 KB

Payload ESP‑NOW: \~200 bytes

Pacotes necessários:

≈ 4000

Tempo médio:

10 -- 30 segundos dependendo da qualidade do link.

------------------------------------------------------------------------

# OTA em Rede Multi‑Hop

OTA pode atravessar repetidores.

    gateway
      ↓
    node relay
      ↓
    node relay
      ↓
    node destino

Os relays apenas retransmitem blocos.

------------------------------------------------------------------------

# Modos de Desenvolvimento

## 1 -- Desenvolvimento local

    PC
     ↓
    USB
     ↓
    ESP32

Compilação rápida.

## 2 -- Teste OTA

    PC
     ↓
    gateway
     ↓
    ESP‑NOW
     ↓
    node

Simula cenário real.

## 3 -- OTA via Bluetooth

    celular
     ↓
    BLE
     ↓
    node

Útil para manutenção em campo.

------------------------------------------------------------------------

# Estratégia de Evolução do Firmware

### Versão 0.1

-   comunicação ESP‑NOW básica
-   gateway USB
-   envio de sensor

### Versão 0.2

-   descriptor de dispositivo
-   auto‑descoberta

### Versão 0.3

-   mesh multi‑hop
-   relay automático

### Versão 0.4

-   OTA

### Versão 0.5

-   configuração via BLE

### Versão 1.0

-   drivers modulares
-   auto‑configuração de sensores

------------------------------------------------------------------------

# Testes com Hardware Real

Com o hardware atual já é possível iniciar.

## Hardware mínimo

    1 ESP32‑S3 → gateway USB
    2 ESP32‑C3 → nodes

## Testes iniciais

1.  comunicação ESP‑NOW entre dois nodes
2.  gateway USB recebendo pacotes
3.  relay entre nodes
4.  mesh simples
5.  OTA em um node

------------------------------------------------------------------------

# Frequência de Sensores

Para reservatórios:

    medição: 30 s
    envio: 120 s
    heartbeat: 60 s

Tráfego de rede permanece muito baixo.

------------------------------------------------------------------------

# Estrutura Recomendada do Firmware

    radio/
    mesh/
    drivers/
    config/
    ota/
    gateway/
    ui/

Benefícios:

-   modular
-   fácil manutenção
-   fácil expansão

------------------------------------------------------------------------

# Integração com Home Assistant

Gateway publica dados via MQTT.

Exemplo:

    agua/n1/nivel
    agua/n2/nivel
    agua/n3/temp
    agua/n4/status

Home Assistant pode usar **MQTT Discovery** para criar entidades
automaticamente.

------------------------------------------------------------------------

# Escalabilidade

Arquitetura suporta facilmente:

    10 nodes
    20 nodes
    50 nodes

pois sensores enviam poucos dados.

------------------------------------------------------------------------

# Ciclo de Desenvolvimento

    escrever código
    ↓
    OTA para node
    ↓
    testar
    ↓
    ajustar
    ↓
    OTA novamente

Sem necessidade de acessar o hardware.

------------------------------------------------------------------------

# Recomendação Importante

Usar **firmware universal para todos os nodes**.

Isso evita:

-   múltiplos firmwares
-   problemas de versão
-   manutenção complexa

O comportamento do node é definido pela **configuração armazenada no
NVS**.

------------------------------------------------------------------------

# Próximos Passos

1.  Implementar comunicação ESP‑NOW básica
2.  Criar gateway USB simples
3.  Implementar descriptor de dispositivo
4.  Criar sistema OTA
5.  Adicionar drivers modulares de sensores
