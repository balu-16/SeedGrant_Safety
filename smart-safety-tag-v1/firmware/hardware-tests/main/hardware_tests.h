#pragma once

#include "esp_err.h"

esp_err_t i2c_test_init(void);
esp_err_t accelerometer_test(void);
esp_err_t fuel_gauge_test(void);
esp_err_t feedback_test_init(void);
void feedback_test_pulse(void);
void sos_test_poll(void);
esp_err_t microphone_test_once(void);
esp_err_t ble_test_start(void);

