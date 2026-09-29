#include "hardware_tests.h"

#include "board_pins.h"
#include <stdbool.h>
#include <stdint.h>
#include "driver/gpio.h"
#include "esp_log.h"
#include "esp_timer.h"

static const char *TAG = "SOS";
static bool was_pressed;
static int64_t last_transition_us;

void sos_test_poll(void)
{
    bool pressed = gpio_get_level(PIN_SOS_N) == 0;
    int64_t now = esp_timer_get_time();
    if (pressed != was_pressed && now - last_transition_us >= 30000) {
        was_pressed = pressed;
        last_transition_us = now;
        ESP_LOGI(TAG, "button %s", pressed ? "pressed" : "released");
        if (pressed) feedback_test_pulse();
    }
}
