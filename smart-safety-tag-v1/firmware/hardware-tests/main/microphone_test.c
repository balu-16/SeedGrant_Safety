#include "hardware_tests.h"

#include <stdint.h>
#include "board_pins.h"
#include "driver/gpio.h"
#include "driver/i2s_pdm.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "soc/soc_caps.h"

static const char *TAG = "PDM_MIC";

esp_err_t microphone_test_once(void)
{
    esp_err_t err;
    i2s_chan_handle_t rx = NULL;
    gpio_set_level(PIN_REGULATOR_MODE, 1); /* Fixed PWM and the 3.0 V microphone LDO. */
    vTaskDelay(pdMS_TO_TICKS(30));
    i2s_chan_config_t channel = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    err = i2s_new_channel(&channel, NULL, &rx);
    if (err != ESP_OK) goto done;

    i2s_pdm_rx_config_t config = {
        .clk_cfg = I2S_PDM_RX_CLK_DEFAULT_CONFIG(AUDIO_PCM_RATE_HZ),
        .slot_cfg = I2S_PDM_RX_SLOT_PCM_FMT_DEFAULT_CONFIG(
            I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .clk = PIN_PDM_CLK,
#if SOC_I2S_PDM_MAX_RX_LINES == 4
            .dins = {PIN_PDM_DATA, GPIO_NUM_NC, GPIO_NUM_NC, GPIO_NUM_NC},
#else
            .din = PIN_PDM_DATA,
#endif
            .invert_flags = {.clk_inv = false},
        },
    };
    config.clk_cfg.dn_sample_mode = I2S_PDM_DSR_16S; /* 16 kHz x 128 = 2.048 MHz. */
    err = i2s_channel_init_pdm_rx_mode(rx, &config);
    if (err != ESP_OK) goto done;
    err = i2s_channel_enable(rx);
    if (err != ESP_OK) goto done;

    for (int window = 0; window < 4; ++window) {
        int16_t samples[1024];
        size_t bytes = 0;
        err = i2s_channel_read(rx, samples, sizeof(samples), &bytes, 1000);
        if (err != ESP_OK) break;
        if (bytes < sizeof(samples) / 2) {
            err = ESP_ERR_INVALID_SIZE;
            break;
        }
        uint64_t sum_squares = 0;
        size_t count = bytes / sizeof(samples[0]);
        for (size_t n = 0; n < count; ++n) {
            int32_t sample = samples[n];
            sum_squares += (uint64_t)(sample * sample);
        }
        ESP_LOGI(TAG, "window %d: %u samples, mean square %llu; speak/tap and compare",
                 window, (unsigned)count, (unsigned long long)(sum_squares / count));
        vTaskDelay(pdMS_TO_TICKS(250));
    }
    i2s_channel_disable(rx);

done:
    if (rx) i2s_del_channel(rx);
    gpio_reset_pin(PIN_PDM_CLK);
    gpio_set_level(PIN_PDM_CLK, 0);
    gpio_set_direction(PIN_PDM_CLK, GPIO_MODE_OUTPUT);
    gpio_set_level(PIN_REGULATOR_MODE, 0);
    return err;
}
