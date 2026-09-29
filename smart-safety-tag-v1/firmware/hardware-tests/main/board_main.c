#include "hardware_tests.h"

#include "board_pins.h"
#include <stdint.h>
#include "driver/gpio.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "nvs_flash.h"

static const char *TAG = "TAG_TEST";

static void log_check(const char *name, esp_err_t err)
{
    if (err == ESP_OK) ESP_LOGI(TAG, "%s: PASS", name);
    else ESP_LOGE(TAG, "%s: FAIL (%s)", name, esp_err_to_name(err));
}

void app_main(void)
{
    log_check("safe output setup", feedback_test_init());
    gpio_config_t inputs = {
        .pin_bit_mask = (1ULL << PIN_SOS_N) | (1ULL << PIN_ACCELEROMETER_INT1) |
                        (1ULL << PIN_ACCELEROMETER_INT2) | (1ULL << PIN_FUEL_ALERT_N) |
                        (1ULL << PIN_CHARGER_STAT1_N) | (1ULL << PIN_CHARGER_STAT2_N),
        .mode = GPIO_MODE_INPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    log_check("input setup", gpio_config(&inputs));
    esp_err_t i2c = i2c_test_init();
    log_check("I2C setup", i2c);
    if (i2c == ESP_OK) {
        log_check("LIS2DW12", accelerometer_test());
        log_check("MAX17048", fuel_gauge_test());
    }
    feedback_test_pulse();
    log_check("PDM audio capture", microphone_test_once());

    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    log_check("NVS setup", err);
    if (err == ESP_OK) log_check("BLE advertising", ble_test_start());

    uint32_t ticks = 0;
    for (;;) {
        sos_test_poll();
        if (++ticks % 200 == 0) {
            ESP_LOGI(TAG, "INT1=%d INT2=%d ALRT=%d STAT1=%d STAT2=%d",
                     gpio_get_level(PIN_ACCELEROMETER_INT1),
                     gpio_get_level(PIN_ACCELEROMETER_INT2),
                     gpio_get_level(PIN_FUEL_ALERT_N),
                     gpio_get_level(PIN_CHARGER_STAT1_N),
                     gpio_get_level(PIN_CHARGER_STAT2_N));
            if (i2c == ESP_OK) {
                log_check("LIS2DW12", accelerometer_test());
                log_check("MAX17048", fuel_gauge_test());
            }
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
