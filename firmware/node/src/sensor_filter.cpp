#include "sensor_filter.h"
#include <string.h>
#include <stdlib.h>

void filter_init(sensor_filter_t *f, uint8_t window, uint8_t outlier_cm) {
    memset(f, 0, sizeof(*f));
    f->window      = window ? window : DEFAULT_FILTER_WINDOW;
    f->outlier_cm  = outlier_cm ? outlier_cm : DEFAULT_OUTLIER_CM;
    f->initialized = false;
}

// Returns filtered average, or 0 if sample was rejected
uint16_t filter_update(sensor_filter_t *f, uint16_t raw) {
    // Layer 1: reject invalid or out-of-range
    if (raw == 0 || raw > HC_MAX_RANGE_CM) return 0;

    // Layer 1: reject outlier (only after buffer has at least one value)
    if (f->initialized) {
        int delta = (int)raw - (int)f->moving_avg;
        if (delta < 0) delta = -delta;
        if (delta > f->outlier_cm) return 0;
    }

    // Layer 2: moving average
    f->buf[f->buf_idx % f->window] = raw;
    f->buf_idx++;
    f->initialized = true;

    uint8_t count = f->buf_idx < f->window ? f->buf_idx : f->window;
    uint32_t sum = 0;
    for (uint8_t i = 0; i < count; i++) sum += f->buf[i];
    f->moving_avg = (uint16_t)((sum + count / 2) / count);  // rounded integer

    return f->moving_avg;
}
