#ifndef PDSX_MULTITASKING_H
#define PDSX_MULTITASKING_H

#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "freertos/timers.h"
#include <map>

//--- Global Veri ve Senkronizasyon Mekanizmalar ---

// Paylalan verilere gvenli eriim iin bir mutex (kilitleme nesnesi)
extern SemaphoreHandle_t pdsx_global_mutex;

// Mutex'i balatmak iin bir fonksiyon
void pdsx_init_mutex();

// Global verilere kilitli eriim iin makrolar
#define PDSX_LOCK() xSemaphoreTake(pdsx_global_mutex, portMAX_DELAY)
#define PDSX_UNLOCK() xSemaphoreGive(pdsx_global_mutex)

//--- Grev Ynetim Fonksiyonlar ---

/**
 * @brief PDSX'teki bir SUB veya EVENT' ayr bir FreeRTOS grevi olarak balatr.
 * @param taskFunction Grevin altraca C++ fonksiyonu.
 * @param taskName Grev iin okunabilir bir isim.
 * @param coreID Grevin atanaca ilemci ekirdei (0 veya 1).
 * @param stackDepth Grevin yn boyutu (varsaylan 4096).
 * @param priority Grevin ncelii (varsaylan 1).
 * @return Oluturulan grevin tantcs (TaskHandle_t). Hata durumunda NULL.
 */
TaskHandle_t pdsx_createTask(TaskFunction_t taskFunction, const char* taskName, int coreID, int stackDepth = 4096, UBaseType_t priority = 1);

/**
 * @brief PDSX'ten gelen bir grevi siler.
 * @param taskHandle Silinecek grevin tantcs.
 */
void pdsx_deleteTask(TaskHandle_t taskHandle);


//--- Zamanlayc Ynetim Fonksiyonlar ---

// Her PDSX EVENT veya SUB' iin bir sarmalayc (wrapper)
typedef void (*PDSXEventHandler_t)();

// Zamanlayc geri ar fonksiyonu iin bilgi saklama yaps
struct PDSXTimerInfo {
    PDSXEventHandler_t handler;
    int count;
    bool isOneShot;
};

// Zamanlayc kimliini ve bilgilerini eletirmek iin bir harita
extern std::map<int, PDSXTimerInfo> pdsx_timer_map;

/**
 * @brief PDSX'teki CONFIGURE TIMER komutunu FreeRTOS zamanlaycsna dntrr.
 * @param timerID PDSX'teki zamanlayc kimlii (haritada saklamak iin).
 * @param intervalMs Zamanlaycnn tetiklenme aral (milisaniye).
 * @param count Zamanlaycnn ka kez alaca (-1 ise sonsuz).
 * @param eventFunction Zamanlayc tetiklendiinde arlacak PDSX EVENT'.
 * @return Oluturulan zamanlaycnn tantcs. Hata durumunda NULL.
 */
TimerHandle_t pdsx_createTimer(int timerID, int intervalMs, int count, PDSXEventHandler_t eventFunction);

#endif // PDSX_MULTITASKING_H