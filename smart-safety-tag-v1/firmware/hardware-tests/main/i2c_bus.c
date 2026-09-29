#include "i2c_bus.h"

#include "board_pins.h"
#include "driver/i2c_master.h"

static i2c_master_bus_handle_t bus;
static i2c_master_dev_handle_t accelerometer;
static i2c_master_dev_handle_t gauge;

static esp_err_t add_device(uint8_t address, i2c_master_dev_handle_t *device)
{
    i2c_device_config_t config = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = address,
        .scl_speed_hz = 400000,
    };
    return i2c_master_bus_add_device(bus, &config, device);
}

esp_err_t i2c_test_init(void)
{
    i2c_master_bus_config_t config = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = false, /* R3/R4 are 4.7 kOhm. */
    };
    esp_err_t err = i2c_new_master_bus(&config, &bus);
    if (err != ESP_OK) return err;
    err = add_device(0x18, &accelerometer); /* LIS2DW12 SA0 tied low. */
    if (err != ESP_OK) return err;
    return add_device(0x36, &gauge);
}

static i2c_master_dev_handle_t device_for(uint8_t address)
{
    if (address == 0x18) return accelerometer;
    if (address == 0x36) return gauge;
    return NULL;
}

esp_err_t i2c_test_read(uint8_t address, uint8_t reg, uint8_t *data, size_t size)
{
    i2c_master_dev_handle_t device = device_for(address);
    if (!device || !data || !size) return ESP_ERR_INVALID_ARG;
    return i2c_master_transmit_receive(device, &reg, 1, data, size, 100);
}

esp_err_t i2c_test_write(uint8_t address, uint8_t reg, uint8_t value)
{
    i2c_master_dev_handle_t device = device_for(address);
    if (!device) return ESP_ERR_INVALID_ARG;
    uint8_t bytes[2] = {reg, value};
    return i2c_master_transmit(device, bytes, sizeof(bytes), 100);
}
