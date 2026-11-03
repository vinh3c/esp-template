#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"

extern "C" void app_main(void)
{
    while (true) {
        ESP_LOGI("app", "Hello world");
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
