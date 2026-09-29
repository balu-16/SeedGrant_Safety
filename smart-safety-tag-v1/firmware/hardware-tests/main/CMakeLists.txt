idf_component_register(
    SRCS "board_main.c" "i2c_bus.c" "accelerometer_test.c" "fuel_gauge_test.c"
         "feedback_test.c" "sos_test.c" "microphone_test.c" "ble_test.c"
    INCLUDE_DIRS "."
    REQUIRES driver esp_driver_gpio esp_driver_i2c esp_driver_i2s bt nvs_flash esp_timer
)
