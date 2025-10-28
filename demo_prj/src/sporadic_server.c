#include "sporadic_server.h"

#include <string.h>

bool sporadic_server_init(sporadic_server_t *server,
                          QueueHandle_t queue,
                          TickType_t period_ticks,
                          TickType_t budget_ticks)
{
    if ((server == NULL) || (queue == NULL) || (period_ticks == 0U) || (budget_ticks == 0U))
    {
        return false;
    }

    server->queue = queue;
    server->period_ticks = period_ticks;
    server->budget_ticks = budget_ticks;
    server->remaining_ticks = budget_ticks;
    server->next_release_tick = 0U;
    return true;
}

sporadic_server_status_t sporadic_server_submit_from_isr(sporadic_server_t *server,
                                                         const void *item,
                                                         size_t item_size,
                                                         TickType_t cost_ticks,
                                                         BaseType_t *hp_task_woken)
{
    if ((server == NULL) || (item == NULL) || (cost_ticks == 0U))
    {
        return SPORADIC_SERVER_NO_BUDGET;
    }

    UBaseType_t saved_interrupt_state = taskENTER_CRITICAL_FROM_ISR();
    TickType_t now = xTaskGetTickCountFromISR();

    if (now >= server->next_release_tick)
    {
        server->remaining_ticks = server->budget_ticks;
        server->next_release_tick = now + server->period_ticks;
    }

    if (server->remaining_ticks < cost_ticks)
    {
        taskEXIT_CRITICAL_FROM_ISR(saved_interrupt_state);
        return SPORADIC_SERVER_NO_BUDGET;
    }

    server->remaining_ticks -= cost_ticks;
    taskEXIT_CRITICAL_FROM_ISR(saved_interrupt_state);

    if (xQueueSendFromISR(server->queue, item, hp_task_woken) != pdPASS)
    {
        /* Refund the budget if the queue is full. */
        saved_interrupt_state = taskENTER_CRITICAL_FROM_ISR();
        server->remaining_ticks += cost_ticks;
        taskEXIT_CRITICAL_FROM_ISR(saved_interrupt_state);
        return SPORADIC_SERVER_QUEUE_FULL;
    }

    return SPORADIC_SERVER_OK;
}
