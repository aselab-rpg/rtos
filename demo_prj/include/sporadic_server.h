#ifndef SPORADIC_SERVER_H
#define SPORADIC_SERVER_H

#include <stdint.h>
#include <stdbool.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "task.h"

typedef struct
{
    QueueHandle_t queue;
    TickType_t period_ticks;
    TickType_t budget_ticks;
    TickType_t remaining_ticks;
    TickType_t next_release_tick;
} sporadic_server_t;

typedef enum
{
    SPORADIC_SERVER_OK = 0,
    SPORADIC_SERVER_NO_BUDGET,
    SPORADIC_SERVER_QUEUE_FULL
} sporadic_server_status_t;

bool sporadic_server_init(sporadic_server_t *server,
                          QueueHandle_t queue,
                          TickType_t period_ticks,
                          TickType_t budget_ticks);

sporadic_server_status_t sporadic_server_submit_from_isr(sporadic_server_t *server,
                                                         const void *item,
                                                         size_t item_size,
                                                         TickType_t cost_ticks,
                                                         BaseType_t *hp_task_woken);

#endif /* SPORADIC_SERVER_H */
