#include "PDSXMultitasking.h"

// --- Global Deikenlerin Tanmlanmas ---
SemaphoreHandle_t pdsx_global_mutex = NULL;
std::map<int, PDSXTimerInfo> pdsx_timer_map;

void pdsx_init_mutex() {
    if (pdsx_global_mutex == NULL) {
        pdsx_global_mutex = xSemaphoreCreateMutex();
    }
}

//--- Grev Ynetim Fonksiyonlar ---

TaskHandle_t pdsx_createTask(TaskFunction_t taskFunction, const char* taskName, int coreID, int stackDepth, UBaseType_t priority) {
    TaskHandle_t taskHandle = NULL;
    BaseType_t result = xTaskCreatePinnedToCore(
        taskFunction,   // Grev fonksiyonu
        taskName,       // Grev ad
        stackDepth,     // Yn boyutu
        NULL,           // Parametreler
        priority,       // ncelik
        &taskHandle,    // Grev tantcs
        coreID          // ekirdek
    );

    if (result != pdPASS) {
        Serial.println("HATA: Grev oluturulamad: " + String(taskName));
        return NULL;
    }
    return taskHandle;
}

void pdsx_deleteTask(TaskHandle_t taskHandle) {
    if (taskHandle != NULL) {
        vTaskDelete(taskHandle);
    }
}

//--- Zamanlayc Ynetim Fonksiyonlar ---

// FreeRTOS zamanlaycs tarafndan arlacak geri arma fonksiyonu
void pdsx_timerCallback(TimerHandle_t xTimer) {
    void* pvTimerID = pvTimerGetTimerID(xTimer);
    int timerID = (int)pvTimerID;

    if (pdsx_timer_map.count(timerID) > 0) {
        PDSXTimerInfo& info = pdsx_timer_map[timerID];
        
        PDSX_LOCK();
        info.handler(); // PDSX EVENT'n ar
        PDSX_UNLOCK();

        if (info.isOneShot) {
            info.count--;
            if (info.count <= 0) {
                xTimerStop(xTimer, 0);
                xTimerDelete(xTimer, 0);
                pdsx_timer_map.erase(timerID);
                Serial.println("Zamanlayc bitti ve silindi: " + String(timerID));
            }
        }
    }
}

TimerHandle_t pdsx_createTimer(int timerID, int intervalMs, int count, PDSXEventHandler_t eventFunction) {
    // Zamanlayc bilgilerini haritada sakla
    pdsx_timer_map[timerID] = { eventFunction, count, (count != -1) };

    bool isOneShot = (count != -1);
    TimerHandle_t newTimer = xTimerCreate(
        "PDSX_Timer",
        pdMS_TO_TICKS(intervalMs),
        !isOneShot, // pdTRUE: Otomatik yeniden ykleme, pdFALSE: Tek seferlik
        (void*)timerID, // Zamanlayc kimliini ID olarak kullan
        pdsx_timerCallback
    );

    if (newTimer != NULL) {
        xTimerStart(newTimer, 0);
    } else {
        Serial.println("HATA: Zamanlayc oluturulamad: " + String(timerID));
    }
    return newTimer;
}