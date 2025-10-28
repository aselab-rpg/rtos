#ifndef APP_TASKS_H
#define APP_TASKS_H

#include "FreeRTOS.h"
#include "queue.h"

#include "app_types.h"

void app_create_tasks(void);

/* ISR hook used by the gateway/app command interrupt. */
void app_command_isr_enqueue(const control_command_t *command_from_isr);

/* Telemetry buffer accessors */
bool app_telemetry_pop(telemetry_entry_t *out_entry, TickType_t wait_ticks);

#endif /* APP_TASKS_H */
