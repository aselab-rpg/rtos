#include "app_tasks.h"

#include <stdio.h>
#include <string.h>

#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

#include "app_config.h"
#include "sporadic_server.h"
#include "ring_buffer.h"

/* Forward declarations for board-level hooks. Replace with concrete drivers. */
static void board_actuator_write(float normalized_pwm);
static sensor_sample_t board_sample_sensors(void);
static void board_led_update(const sensor_sample_t *sample, float pid_output);
static bool board_database_flush(const telemetry_entry_t *entries, size_t count, TickType_t relative_deadline);

static void control_task(void *pvParameters);
static void sensor_task(void *pvParameters);
static void led_task(void *pvParameters);
static void database_task(void *pvParameters);
static void command_task(void *pvParameters);

static float pid_step(pid_controller_t *pid, float measurement, float dt_seconds);
static void telemetry_store(const telemetry_entry_t *entry);

static QueueHandle_t gSensorQueue;
static QueueHandle_t gCommandQueue;
static QueueHandle_t gSetpointMailbox;

static sporadic_server_t gSporadicServer;

static ring_buffer_t gTelemetryBuffer;
static uint8_t gTelemetryStorage[TELEMETRY_RING_DEPTH * sizeof(telemetry_entry_t)];

static sensor_sample_t gLastSensorSample;
static control_command_t gActiveCommand;
static pid_controller_t gPid;

void app_create_tasks(void)
{
    gSensorQueue = xQueueCreate(SENSOR_QUEUE_DEPTH, sizeof(sensor_sample_t));
    configASSERT(gSensorQueue != NULL);

    gCommandQueue = xQueueCreate(COMMAND_QUEUE_DEPTH, sizeof(control_command_t));
    configASSERT(gCommandQueue != NULL);

    gSetpointMailbox = xQueueCreate(1U, sizeof(control_command_t));
    configASSERT(gSetpointMailbox != NULL);

    bool ring_ok = ring_buffer_init(&gTelemetryBuffer,
                                    gTelemetryStorage,
                                    sizeof(telemetry_entry_t),
                                    TELEMETRY_RING_DEPTH);
    configASSERT(ring_ok == true);

    bool sporadic_ok = sporadic_server_init(&gSporadicServer,
                                            gCommandQueue,
                                            APP_MS_TO_TICKS(SPORADIC_SERVER_PERIOD_MS),
                                            APP_MS_TO_TICKS(SPORADIC_SERVER_BUDGET_MS));
    configASSERT(sporadic_ok == true);

    memset(&gLastSensorSample, 0, sizeof(gLastSensorSample));
    gActiveCommand.desired_temperature_c = 22.0f;
    gActiveCommand.desired_humidity_pct = 60.0f;
    gActiveCommand.desired_rpm = 1200.0f;
    gActiveCommand.timestamp = xTaskGetTickCount();

    gPid.kp = 1.2f;
    gPid.ki = 0.4f;
    gPid.kd = 0.05f;
    gPid.integral = 0.0f;
    gPid.previous_error = 0.0f;
    gPid.setpoint = gActiveCommand.desired_temperature_c;

    BaseType_t ok;
    ok = xTaskCreate(control_task,
                     "CTRL",
                     CONTROL_TASK_STACK_WORDS,
                     NULL,
                     CONTROL_TASK_PRIORITY,
                     NULL);
    configASSERT(ok == pdPASS);

    ok = xTaskCreate(sensor_task,
                     "SENS",
                     SENSOR_TASK_STACK_WORDS,
                     NULL,
                     SENSOR_TASK_PRIORITY,
                     NULL);
    configASSERT(ok == pdPASS);

    ok = xTaskCreate(led_task,
                     "LED",
                     LED_TASK_STACK_WORDS,
                     NULL,
                     LED_TASK_PRIORITY,
                     NULL);
    configASSERT(ok == pdPASS);

    ok = xTaskCreate(database_task,
                     "DB",
                     DATABASE_TASK_STACK_WORDS,
                     NULL,
                     DATABASE_TASK_PRIORITY,
                     NULL);
    configASSERT(ok == pdPASS);

    ok = xTaskCreate(command_task,
                     "CMD",
                     COMMAND_TASK_STACK_WORDS,
                     NULL,
                     COMMAND_TASK_PRIORITY,
                     NULL);
    configASSERT(ok == pdPASS);
}

void app_command_isr_enqueue(const control_command_t *command_from_isr)
{
    if (command_from_isr == NULL)
    {
        return;
    }

    control_command_t local_copy = *command_from_isr;
    local_copy.timestamp = xTaskGetTickCountFromISR();

    BaseType_t higher_priority_task_woken = pdFALSE;
    sporadic_server_status_t status = sporadic_server_submit_from_isr(&gSporadicServer,
                                                                      &local_copy,
                                                                      sizeof(local_copy),
                                                                      APP_MS_TO_TICKS(COMMAND_ISR_COST_MS),
                                                                      &higher_priority_task_woken);

    if (status == SPORADIC_SERVER_OK)
    {
        portYIELD_FROM_ISR(higher_priority_task_woken);
    }
}

bool app_telemetry_pop(telemetry_entry_t *out_entry, TickType_t wait_ticks)
{
    (void)wait_ticks;
    if (out_entry == NULL)
    {
        return false;
    }

    taskENTER_CRITICAL();
    bool result = ring_buffer_pop(&gTelemetryBuffer, out_entry);
    taskEXIT_CRITICAL();
    return result;
}

static void control_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t period_ticks = APP_MS_TO_TICKS(CONTROL_TASK_PERIOD_MS);
    TickType_t next_release = xTaskGetTickCount();

    for (;;)
    {
        vTaskDelayUntil(&next_release, period_ticks);

        sensor_sample_t latest_sample;
        while (xQueueReceive(gSensorQueue, &latest_sample, 0) == pdPASS)
        {
            gLastSensorSample = latest_sample;
        }
        latest_sample = gLastSensorSample;

        control_command_t latest_command = gActiveCommand;
        if (xQueueReceive(gSetpointMailbox, &latest_command, 0) == pdPASS)
        {
            gActiveCommand = latest_command;
            gPid.setpoint = latest_command.desired_temperature_c;
        }

        const float dt = (float)CONTROL_TASK_PERIOD_MS / 1000.0f;
        float pid_output = pid_step(&gPid, latest_sample.temperature_c, dt);
        board_actuator_write(pid_output);

        telemetry_entry_t entry = {
            .timestamp = xTaskGetTickCount(),
            .pid_output = pid_output,
            .latest_sample = latest_sample,
            .latest_command = gActiveCommand};
        telemetry_store(&entry);
    }
}

static void sensor_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t period_ticks = APP_MS_TO_TICKS(SENSOR_TASK_PERIOD_MS);
    TickType_t next_release = xTaskGetTickCount();

    for (;;)
    {
        vTaskDelayUntil(&next_release, period_ticks);

        sensor_sample_t sample = board_sample_sensors();
        sample.timestamp = xTaskGetTickCount();

        if (xQueueSend(gSensorQueue, &sample, 0) != pdPASS)
        {
            sensor_sample_t discarded;
            (void)xQueueReceive(gSensorQueue, &discarded, 0);
            (void)xQueueSend(gSensorQueue, &sample, 0);
        }
    }
}

static void led_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t period_ticks = APP_MS_TO_TICKS(LED_TASK_PERIOD_MS);
    TickType_t next_release = xTaskGetTickCount();

    for (;;)
    {
        vTaskDelayUntil(&next_release, period_ticks);
        board_led_update(&gLastSensorSample, gPid.previous_error);
    }
}

static void database_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t period_ticks = APP_MS_TO_TICKS(DATABASE_TASK_PERIOD_MS);
    TickType_t next_release = xTaskGetTickCount();

    telemetry_entry_t batch[16];

    for (;;)
    {
        vTaskDelayUntil(&next_release, period_ticks);

        size_t count = 0U;
        while ((count < (sizeof(batch) / sizeof(batch[0]))) && app_telemetry_pop(&batch[count], 0))
        {
            count++;
        }

        if (count == 0U)
        {
            continue;
        }

        const TickType_t soft_deadline = APP_MS_TO_TICKS(200U);
        (void)board_database_flush(batch, count, soft_deadline);
    }
}

static void command_task(void *pvParameters)
{
    (void)pvParameters;
    const TickType_t poll_ticks = APP_MS_TO_TICKS(COMMAND_SERVER_POLL_MS);

    for (;;)
    {
        control_command_t new_command;
        if (xQueueReceive(gCommandQueue, &new_command, poll_ticks) == pdPASS)
        {
            (void)xQueueOverwrite(gSetpointMailbox, &new_command);
        }
    }
}

static float pid_step(pid_controller_t *pid, float measurement, float dt_seconds)
{
    if ((pid == NULL) || (dt_seconds <= 0.0f))
    {
        return 0.0f;
    }

    const float error = pid->setpoint - measurement;
    pid->integral += error * dt_seconds;

    const float integral_limit = 100.0f;
    if (pid->integral > integral_limit)
    {
        pid->integral = integral_limit;
    }
    else if (pid->integral < -integral_limit)
    {
        pid->integral = -integral_limit;
    }

    const float derivative = (error - pid->previous_error) / dt_seconds;
    pid->previous_error = error;

    float output = (pid->kp * error) + (pid->ki * pid->integral) + (pid->kd * derivative);

    if (output > 1.0f)
    {
        output = 1.0f;
    }
    else if (output < 0.0f)
    {
        output = 0.0f;
    }

    return output;
}

static void telemetry_store(const telemetry_entry_t *entry)
{
    if (entry == NULL)
    {
        return;
    }

    taskENTER_CRITICAL();
    if (!ring_buffer_push(&gTelemetryBuffer, entry))
    {
        telemetry_entry_t discarded;
        (void)ring_buffer_pop(&gTelemetryBuffer, &discarded);
        (void)ring_buffer_push(&gTelemetryBuffer, entry);
    }
    taskEXIT_CRITICAL();
}

static void board_actuator_write(float normalized_pwm)
{
    (void)normalized_pwm;
    /* Hook into PWM driver here. */
}

static sensor_sample_t board_sample_sensors(void)
{
    sensor_sample_t sample;
    sample.timestamp = 0;
    sample.temperature_c = 25.0f;
    sample.humidity_pct = 55.0f;
    sample.rpm = 1000.0f;
    return sample;
}

static void board_led_update(const sensor_sample_t *sample, float pid_output)
{
    (void)sample;
    (void)pid_output;
    /* Map telemetry to LED states as needed. */
}

static bool board_database_flush(const telemetry_entry_t *entries, size_t count, TickType_t relative_deadline)
{
    (void)relative_deadline;
    if ((entries == NULL) || (count == 0U))
    {
        return false;
    }

    for (size_t i = 0; i < count; i++)
    {
        const telemetry_entry_t *entry = &entries[i];
        printf("DB push t=%lu temp=%.2f rpm=%.2f pwm=%.2f\n",
               (unsigned long)entry->timestamp,
               entry->latest_sample.temperature_c,
               entry->latest_sample.rpm,
               entry->pid_output);
    }
    return true;
}
