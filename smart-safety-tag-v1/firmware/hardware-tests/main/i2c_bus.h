#pragma once

#include <stddef.h>
#include <stdint.h>
#include "esp_err.h"

esp_err_t i2c_test_init(void);
esp_err_t i2c_test_read(uint8_t address, uint8_t reg, uint8_t *data, size_t size);
esp_err_t i2c_test_write(uint8_t address, uint8_t reg, uint8_t value);

