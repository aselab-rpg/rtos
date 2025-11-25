#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include "FreeRTOS.h"

/* Scheduler settings */
#define APP_TICK_RATE_HZ             1000U

/* Task periods in milliseconds */
#define CONTROL_TASK_PERIOD_MS        20U
#define SENSOR_TASK_PERIOD_MS        100U
#define LED_TASK_PERIOD_MS           200U
#define DATABASE_TASK_PERIOD_MS     1000U
#define COMMAND_SERVER_POLL_MS        10U

/* Estimated worst-case execution (budget) per activation */
#define CONTROL_TASK_BUDGET_MS         2U
#define SENSOR_TASK_BUDGET_MS          2U
#define LED_TASK_BUDGET_MS             1U
#define DATABASE_TASK_BUDGET_MS        5U
#define COMMAND_ISR_COST_MS            2U

/* Task stack sizes (words, not bytes) */
#define CONTROL_TASK_STACK_WORDS     512U
#define SENSOR_TASK_STACK_WORDS      512U
#define LED_TASK_STACK_WORDS         256U
#define DATABASE_TASK_STACK_WORDS    768U
#define COMMAND_TASK_STACK_WORDS     512U

/* Task priorities (higher number = higher priority) */
#define CONTROL_TASK_PRIORITY          5U
#define SENSOR_TASK_PRIORITY           4U
#define COMMAND_TASK_PRIORITY          4U
#define LED_TASK_PRIORITY              3U
#define DATABASE_TASK_PRIORITY         2U

/* Queue and buffer sizing */
#define SENSOR_QUEUE_DEPTH            16U
#define COMMAND_QUEUE_DEPTH           10U
#define TELEMETRY_RING_DEPTH         128U

/* Sporadic server parameters for command arrivals */
#define SPORADIC_SERVER_PERIOD_MS      50U
#define SPORADIC_SERVER_BUDGET_MS       2U

/* Helper to convert milliseconds to ticks with compile-time guard */
#define APP_MS_TO_TICKS(ms) ((TickType_t)pdMS_TO_TICKS((ms)))

#endif /* APP_CONFIG_H */
