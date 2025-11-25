#include <stdio.h>

#include "FreeRTOS.h"
#include "task.h"

#include "app_config.h"
#include "app_tasks.h"

static void prv_setup_clocks(void);
static void prv_setup_peripherals(void);

int main(void)
{
    prv_setup_clocks();
    prv_setup_peripherals();

    app_create_tasks();

    vTaskStartScheduler();

    for (;;)
    {
        /* Should never reach here. */
    }
}

static void prv_setup_clocks(void)
{
    /* Configure MCU clocks here. */
}

static void prv_setup_peripherals(void)
{
    /* Initialize GPIO, ADC, UART, PWM, etc. */
    printf("System init complete. Starting scheduler.\n");
}
