# Correções de Overflow — Firmware Node v3.2

## Problemas Identificados

### 1. Overflow de `uint32_t` em contadores de tempo (49 dias)
**Local**: `firmware/node/src/main.cpp`

`uint32_t` armazena milissegundos e faz overflow após **2^32 ms ≈ 49.7 dias**.

Comparações do tipo:
```cpp
if (ms - last_send_ms >= threshold) { ... }  // ❌ Falha no overflow
```

**Sintomas**:
- Nodes param de enviar dados após ~49 dias de uptime
- Heartbeats não enviados
- Mesh neighbors expiram incorretamente
- Daily restart não funciona após overflow

### 2. Bug no Daily Restart
**Local**: `firmware/node/src/main.cpp` linha 283

```cpp
static uint32_t boot_ms = now_ms();  // ❌ Salva tempo de boot
...
if (ms - boot_ms >= 86400000UL) {    // ❌ Falha após overflow
```

**Problema**: Após 49 dias, `ms` faz wrap-around e fica menor que `boot_ms`, fazendo a comparação falhar permanentemente.

### 3. Unidades inconsistentes no Mesh
**Local**: `firmware/node/src/mesh.cpp`

```cpp
// update_neighbor salvava em MILISSEGUNDOS
s_neighbors[i].last_seen = (uint32_t)(esp_timer_get_time() / 1000);

// expire_neighbors lia em SEGUNDOS (dividindo por 1000000 e depois por 1000)
uint32_t now_s = (uint32_t)(esp_timer_get_time() / 1000000);
uint32_t last_s = s_neighbors[i].last_seen / 1000;
```

**Resultado**: Neighbors expiravam 1000x mais rápido que o esperado.

## Correções Aplicadas

### 1. Comparações overflow-safe (`main.cpp`)

**Antes**:
```cpp
if (ms - st->last_send_ms >= threshold) { ... }
```

**Depois**:
```cpp
uint32_t elapsed = ms - st->last_send_ms;  // ✅ Overflow-safe
if (elapsed >= threshold) { ... }
```

**Por que funciona**: Em C/C++, subtração de `unsigned` com wrap-around é definida pelo padrão. Se `ms=100` e `last=4294967290` (perto do overflow), a subtração `100 - 4294967290` resulta em `110` (wrap-around correto).

### 2. Daily restart corrigido

**Antes**:
```cpp
static uint32_t boot_ms = now_ms();  // ❌
if (ms - boot_ms >= 86400000UL) { esp_restart(); }
```

**Depois**:
```cpp
static uint32_t last_restart_check_ms = 0;  // ✅
uint32_t elapsed = ms - last_restart_check_ms;
if (elapsed >= 86400000UL) {
    last_restart_check_ms = ms;  // Reset para próximo ciclo
    esp_restart();
}
```

Agora reinicia a cada 24h independente de overflow.

### 3. Mesh: unidades consistentes e overflow-safe

**Antes**:
```cpp
// Unidades misturadas + overflow unsafe
uint32_t now_s = (uint32_t)(esp_timer_get_time() / 1000000);
uint32_t last_s = s_neighbors[i].last_seen / 1000;
if (now_s - last_s > timeout_s) { ... }  // ❌
```

**Depois**:
```cpp
// Tudo em milissegundos + overflow-safe
uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
s_neighbors[i].last_seen = now_ms;  // Salva em ms

uint32_t elapsed = now_ms - s_neighbors[i].last_seen;  // ✅
if (elapsed > timeout_ms) { ... }
```

## Validação

### Build Status
```
✅ esp32-c3-supermini          SUCCESS   00:00:05.038
✅ esp32-c3-supermini-release  SUCCESS   00:00:04.596
✅ node3-cb3                   SUCCESS   00:00:04.409
```

### Tamanho do Firmware
- RAM:   11.1% (36396 / 327680 bytes)
- Flash: 61.3% (963575 / 1572864 bytes)

## Testes Recomendados

1. **Teste de overflow simulado**: modificar `now_ms()` para retornar `UINT32_MAX - 1000` e verificar comportamento
2. **Uptime prolongado**: deixar node rodando por 50+ dias
3. **Daily restart**: verificar que reinicia corretamente após 24h

## Referências

- **ESP-IDF Timer**: esp_timer_get_time() retorna `int64_t` em **microsegundos**
- **Overflow handling**: C standard §6.2.5/9 - unsigned integer wrap-around é bem definido
- **Best practice**: sempre use `elapsed = now - last` em vez de `now - last >= threshold` diretamente

## Arquivos Modificados

- `firmware/node/src/main.cpp` - correções em `sensor_tick()` e `loop()`
- `firmware/node/src/mesh.cpp` - correções em `mesh_update_neighbor()` e `mesh_expire_neighbors()`

---

**Data**: 2026-03-13  
**Commit**: Overflow fixes - safe uptime >49 days, consistent time units, daily restart fixed
