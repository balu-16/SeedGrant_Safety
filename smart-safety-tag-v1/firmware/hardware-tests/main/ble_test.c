#include "hardware_tests.h"

#include <string.h>
#include "esp_log.h"
#include "host/ble_hs.h"
#include "host/util/util.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"

static const char *TAG = "BLE_TEST";
static uint8_t own_addr_type;

static int gap_event(struct ble_gap_event *event, void *arg);

static void advertise(void)
{
    const char *name = ble_svc_gap_device_name();
    struct ble_hs_adv_fields fields = {0};
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    fields.name = (uint8_t *)name;
    fields.name_len = strlen(name);
    fields.name_is_complete = 1;
    int rc = ble_gap_adv_set_fields(&fields);
    if (rc) {
        ESP_LOGE(TAG, "advertisement fields failed: %d", rc);
        return;
    }
    struct ble_gap_adv_params params = {0};
    params.conn_mode = BLE_GAP_CONN_MODE_UND;
    params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    rc = ble_gap_adv_start(own_addr_type, NULL, BLE_HS_FOREVER, &params, gap_event, NULL);
    if (rc) ESP_LOGE(TAG, "advertising failed: %d", rc);
}

static int gap_event(struct ble_gap_event *event, void *arg)
{
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        ESP_LOGI(TAG, "connection status=%d", event->connect.status);
        if (event->connect.status != 0) advertise();
        break;
    case BLE_GAP_EVENT_DISCONNECT:
        ESP_LOGI(TAG, "disconnected, reason=%d", event->disconnect.reason);
        advertise();
        break;
    case BLE_GAP_EVENT_ADV_COMPLETE:
        advertise();
        break;
    default:
        break;
    }
    return 0;
}

static void on_sync(void)
{
    int rc = ble_hs_util_ensure_addr(0);
    if (rc == 0) rc = ble_hs_id_infer_auto(0, &own_addr_type);
    if (rc == 0) advertise();
    else ESP_LOGE(TAG, "address setup failed: %d", rc);
}

static void host_task(void *argument)
{
    nimble_port_run();
    nimble_port_freertos_deinit();
}

esp_err_t ble_test_start(void)
{
    esp_err_t err = nimble_port_init();
    if (err != ESP_OK) return err;
    ble_hs_cfg.sync_cb = on_sync;
    ble_svc_gap_init();
    ble_svc_gatt_init();
    int rc = ble_svc_gap_device_name_set("SafetyTag-HW");
    if (rc != 0) return ESP_FAIL;
    nimble_port_freertos_init(host_task);
    return ESP_OK;
}
