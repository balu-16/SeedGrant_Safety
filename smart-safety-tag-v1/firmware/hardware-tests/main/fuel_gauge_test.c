#include "hardware_tests.h"

#include "i2c_bus.h"
#include "esp_log.h"

static const char *TAG = "MAX17048";

esp_err_t fuel_gauge_test(void)
{
    uint8_t voltage[2], soc[2];
    esp_err_t err = i2c_test_read(0x36, 0x02, voltage, sizeof(voltage));
    if (err != ESP_OK) return err;
    err = i2c_test_read(0x36, 0x04, soc, sizeof(soc));
    if (err != ESP_OK) return err;
    uint16_t voltage_raw = ((uint16_t)voltage[0] << 8) | voltage[1];
    uint16_t soc_raw = ((uint16_t)soc[0] << 8) | soc[1];
    /* MAX17048 VCELL LSb=78.125 uV; SOC LSb=1/256 percent. */
    ESP_LOGI(TAG, "VCELL=%.3f V, SOC=%.1f%%, ALRT pin read separately",
             voltage_raw * 0.000078125, soc_raw / 256.0);
    return ESP_OK;
}
