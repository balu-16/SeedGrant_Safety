#include "hardware_tests.h"

#include "i2c_bus.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "LIS2DW12";

esp_err_t accelerometer_test(void)
{
    uint8_t id = 0;
    esp_err_t err = i2c_test_read(0x18, 0x0F, &id, 1);
    if (err != ESP_OK) return err;
    if (id != 0x44) {
        ESP_LOGE(TAG, "WHO_AM_I=0x%02x; expected 0x44", id);
        return ESP_FAIL;
    }
    err = i2c_test_write(0x18, 0x21, 0x0C); /* BDU and address auto-increment. */
    if (err != ESP_OK) return err;
    /* 50 Hz, low-power mode 1. The production wake threshold is not set here. */
    err = i2c_test_write(0x18, 0x20, 0x40);
    if (err != ESP_OK) return err;
    vTaskDelay(pdMS_TO_TICKS(100));
    uint8_t raw[6];
    err = i2c_test_read(0x18, 0x28, raw, sizeof(raw));
    if (err != ESP_OK) return err;
    int16_t x = (int16_t)((raw[1] << 8) | raw[0]);
    int16_t y = (int16_t)((raw[3] << 8) | raw[2]);
    int16_t z = (int16_t)((raw[5] << 8) | raw[4]);
    ESP_LOGI(TAG, "WHO_AM_I=0x44, raw X=%d Y=%d Z=%d; tilt and check change", x, y, z);
    return ESP_OK;
}
