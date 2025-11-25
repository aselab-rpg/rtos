#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

LOG_MODULE_REGISTER(msgq_lab, LOG_LEVEL_INF);

#define SERVER_STACK_SIZE 1024
#define CLIENT_STACK_SIZE 1024

struct msg_payload {
    uint32_t seq;
    int64_t sent_ms;
};

K_MSGQ_DEFINE(message_queue, sizeof(struct msg_payload), CONFIG_APP_QUEUE_DEPTH, 4);

static K_THREAD_STACK_DEFINE(server_stack, SERVER_STACK_SIZE);
static K_THREAD_STACK_DEFINE(client_stack, CLIENT_STACK_SIZE);
static struct k_thread server_thread;
static struct k_thread client_thread;
static atomic_t dropped_messages = ATOMIC_INIT(0);

static void busy_sleep_ms(int32_t duration_ms) {
    if (duration_ms <= 0) {
        return;
    }
    k_busy_wait(duration_ms * 1000);
}

static void server_entry(void *p1, void *p2, void *p3) {
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    for (;;) {
        struct msg_payload msg;
        int ret = k_msgq_get(&message_queue, &msg, K_FOREVER);
        if (ret != 0) {
            LOG_ERR("k_msgq_get failed: %d", ret);
            continue;
        }

        int64_t now_ms = k_uptime_get();
        int32_t backlog = k_msgq_num_used_get(&message_queue);
        int64_t latency = now_ms - msg.sent_ms;
        if (latency < 0) {
            latency = 0;
        }

        LOG_INF("server seq=%u latency=%lld ms backlog=%d dropped=%d",
                msg.seq,
                latency,
                backlog,
                atomic_get(&dropped_messages));

        busy_sleep_ms(CONFIG_APP_SERVER_WORK_MS);
    }
}

static void client_entry(void *p1, void *p2, void *p3) {
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    uint32_t seq = 0;
    while (true) {
        struct msg_payload msg = {
            .seq = seq++,
            .sent_ms = k_uptime_get(),
        };

        int ret = k_msgq_put(&message_queue, &msg, K_NO_WAIT);
        if (ret != 0) {
            atomic_inc(&dropped_messages);
            LOG_WRN("queue full, drop seq=%u (drops=%d)",
                    msg.seq,
                    atomic_get(&dropped_messages));
        }

        k_msleep(CONFIG_APP_CLIENT_PERIOD_MS);
    }
}

void main(void) {
    LOG_INF("LAB4 msgq demo start: server prio=%d client prio=%d",
            CONFIG_APP_SERVER_PRIORITY,
            CONFIG_APP_CLIENT_PRIORITY);

    k_thread_create(&server_thread,
                    server_stack,
                    K_THREAD_STACK_SIZEOF(server_stack),
                    server_entry,
                    NULL,
                    NULL,
                    NULL,
                    K_PRIO_PREEMPT(CONFIG_APP_SERVER_PRIORITY),
                    0,
                    K_NO_WAIT);
    k_thread_name_set(&server_thread, "server");

    k_thread_create(&client_thread,
                    client_stack,
                    K_THREAD_STACK_SIZEOF(client_stack),
                    client_entry,
                    NULL,
                    NULL,
                    NULL,
                    K_PRIO_PREEMPT(CONFIG_APP_CLIENT_PRIORITY),
                    0,
                    K_NO_WAIT);
    k_thread_name_set(&client_thread, "client");
}
