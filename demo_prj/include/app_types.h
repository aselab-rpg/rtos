#ifndef APP_TYPES_H
#define APP_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#include "FreeRTOS.h"

typedef struct
{
    TickType_t timestamp;
    float temperature_c;
    float humidity_pct;
    float rpm;
} sensor_sample_t;

typedef struct
{
    TickType_t timestamp;
    float desired_temperature_c;
    float desired_humidity_pct;
    float desired_rpm;
} control_command_t;

typedef struct
{
    TickType_t timestamp;
    float pid_output;
    sensor_sample_t latest_sample;
    control_command_t latest_command;
} telemetry_entry_t;

typedef struct
{
    float kp;
    float ki;
    float kd;
    float setpoint;
    float integral;
    float previous_error;
} pid_controller_t;

#endif /* APP_TYPES_H */
