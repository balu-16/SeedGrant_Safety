#include "hardware_tests.h"

#include "board_pins.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

esp_err_t feedback_test_init(void)
{
    const uint64_t outputs = (1ULL << PIN_LED_RED_N) | (1ULL << PIN_LED_GREEN_N) |
                             (1ULL << PIN_LED_BLUE_N) | (1ULL << PIN_MOTOR_GATE) |
                             (1ULL << PIN_MOTOR_SUPPLY_ENABLE) |
                             (1ULL << PIN_REGULATOR_MODE) | (1ULL << PIN_CHARGE_INHIBIT) |
                             (1ULL << PIN_PDM_CLK);
    gpio_config_t config = {
        .pin_bit_mask = outputs,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    esp_err_t err = gpio_config(&config);
    if (err != ESP_OK) return err;
    gpio_set_level(PIN_LED_RED_N, 1);
    gpio_set_level(PIN_LED_GREEN_N, 1);
    gpio_set_level(PIN_LED_BLUE_N, 1);
    gpio_set_level(PIN_MOTOR_GATE, 0);
    gpio_set_level(PIN_MOTOR_SUPPLY_ENABLE, 0);
    gpio_set_level(PIN_REGULATOR_MODE, 0);
    gpio_set_level(PIN_PDM_CLK, 0);
    gpio_set_level(PIN_CHARGE_INHIBIT, 0); /* Hardware thermal window remains authoritative. */
    return ESP_OK;
}

void feedback_test_pulse(void)
{
    gpio_set_level(PIN_LED_RED_N, 0);
    gpio_set_level(PIN_MOTOR_SUPPLY_ENABLE, 1);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(PIN_MOTOR_GATE, 1);
    vTaskDelay(pdMS_TO_TICKS(120));
    gpio_set_level(PIN_MOTOR_GATE, 0);
    gpio_set_level(PIN_MOTOR_SUPPLY_ENABLE, 0);
    gpio_set_level(PIN_LED_RED_N, 1);
    gpio_set_level(PIN_LED_GREEN_N, 0);
    vTaskDelay(pdMS_TO_TICKS(100));
    gpio_set_level(PIN_LED_GREEN_N, 1);
    gpio_set_level(PIN_LED_BLUE_N, 0);
    vTaskDelay(pdMS_TO_TICKS(100));
    gpio_set_level(PIN_LED_BLUE_N, 1);
}
