# Backup Firmware v3.5.0 → v3.6.0

Data: 15/03/2026

## Mudanças na v3.6.0

### ✅ Funcionalidades Mantidas (100%)
- ✅ Node ID = 2 últimos bytes do MAC (linha 218: `node_id = (mac[4] << 8) | mac[5]`)
- ✅ Suporte a 2 sensores por node (loop em `for (int i = 0; i < 2; i++)`)
- ✅ Relay mode (num_sensors=0) com anti-duplicação
- ✅ Sensor mode (num_sensors=1 ou 2)
- ✅ ESP-NOW mesh com TTL e neighbor tracking
- ✅ NVS config completo
- ✅ Mediana com 5 samples
- ✅ Cálculo de percentual (distance - min) / (max - min) * 100
- ✅ Transmissão distance_cm + percent
- ✅ Todos os comandos (CMD_RESTART, CMD_CONFIG)
- ✅ HELLO packets
- ✅ VBAT reading
- ✅ LED feedback

### 📝 Alterações
1. **Intervalo**: 10s → 60s (linha 173: `if (now - last_read_ms[idx] < 60000)`)
2. **Bug crítico corrigido**: Percentual agora vai no campo `reserved`, não `flags`
   - Antes: `send_packet(PKT_SENSOR, sid, distance_cm, reading.percent)` com `flags = percent`
   - Depois: `send_packet(PKT_SENSOR, sid, distance_cm, reading.percent)` com `reserved = percent`
3. **Versão**: "3.5.0" → "3.6.0"

### ❌ Código Removido (apenas experimental)
- `#define ULTRASONIC_TEST_MODE` e todo código `#if ULTRASONIC_TEST_MODE`
- Função `test_ultrasonic_loop()` (~60 linhas de código experimental)
- Banner ASCII "MODO EXPERIMENTAL DE TESTES ULTRASSÔNICOS"
- Variável não usada `g_last_measure_check_ms`
- Include duplicado de `ultrasonic_experiments.h`

### 📊 Recursos
- **RAM**: 11.1% (36332 bytes) - mantido igual
- **Flash**: 61.3% (963915 bytes) - reduzido ~2 bytes
- **Compilação**: 13.26 segundos

## Nodes Compatíveis
| node_id | alias | Sensors | Status |
|---------|-------|---------|--------|
| 0x7758 | CON | 1 | ✅ Testado v3.6 |
| 0xEE02 | CAV | 1 | Pendente |
| 0x2EC4 | CB31/CB32 | 2 | Pendente |
| 0x9EAC | CIE1/CIE2 | 2 | Pendente |
| 0x3456 | CBIF1/CBIF2 | 2 | Pendente |

## Comparação de Output

### v3.5.0 (10s, bug no flags)
```
S1 dist: 220 cm, 47%
TX type=0x01 sid=1 dist=220 seq=1   ← flags=47 (BUG!)
```

### v3.6.0 (60s, reserved correto)
```
S1 dist: 220 cm, 47%
TX type=0x01 sid=1 dist=220 seq=1   ← reserved=47, flags=0 (CORRETO!)
```

## Arquivo Original
`main_v3.5.cpp` - Firmware completo da versão 3.5.0 para referência
