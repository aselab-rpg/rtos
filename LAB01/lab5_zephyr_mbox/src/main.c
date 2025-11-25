#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

#include <string.h>

LOG_MODULE_REGISTER(mbox_lab, LOG_LEVEL_INF);

#define SERVER_STACK_SIZE 1024
#define CLIENT_STACK_SIZE 1024

struct mail_packet {
    uint32_t seq;
    int64_t sent_ms;
    uint8_t payload[CONFIG_APP_PAYLOAD_BYTES];
};

K_MBOX_DEFINE(work_mbox);
K_SEM_DEFINE(done_sem, 0, 64);

static K_THREAD_STACK_DEFINE(server_stack, SERVER_STACK_SIZE);
static K_THREAD_STACK_DEFINE(client_stack, CLIENT_STACK_SIZE);
static struct k_thread server_thread;
static struct k_thread client_thread;
static atomic_t truncated_msgs = ATOMIC_INIT(0);

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
        struct k_mbox_msg msg = {
            .rx_source_thread = K_ANY,
        };
        struct mail_packet packet;

        int ret = k_mbox_get(&work_mbox, &msg, K_FOREVER);
        if (ret != 0) {
            LOG_ERR("k_mbox_get failed: %d", ret);
            continue;
        }

        if (msg.size > sizeof(packet)) {
            atomic_inc(&truncated_msgs);
            LOG_WRN("payload truncated from %zu to %zu bytes (total trunc=%d)",
                    (size_t)msg.size,
                    sizeof(packet),
                    atomic_get(&truncated_msgs));
            msg.size = sizeof(packet);
        }

        ret = k_mbox_data_get(&msg, &packet);
        if (ret != 0) {
            LOG_ERR("k_mbox_data_get failed: %d", ret);
            continue;
        }

        int64_t now_ms = k_uptime_get();
        int64_t latency_ms = now_ms - packet.sent_ms;
        if (latency_ms < 0) {
            latency_ms = 0;
        }

        LOG_INF("server handled seq=%u latency=%lld ms payload=%zu B truncated=%d",
                packet.seq,
                latency_ms,
                (size_t)msg.size,
                atomic_get(&truncated_msgs));

        busy_sleep_ms(CONFIG_APP_SERVER_WORK_MS);
        k_sem_give(&done_sem);
    }
}

static void client_entry(void *p1, void *p2, void *p3) {
    ARG_UNUSED(p1);
    ARG_UNUSED(p2);
    ARG_UNUSED(p3);

    uint32_t seq = 0;

    while (true) {
        const uint32_t burst_start_seq = seq;
        const int64_t burst_start_ms = k_uptime_get();

        for (int i = 0; i < CONFIG_APP_CLIENT_BURST; ++i) {
            struct mail_packet packet;
            packet.seq = seq++;
            packet.sent_ms = k_uptime_get();
            memset(packet.payload, 0xA5, sizeof(packet.payload));

            struct k_mbox_msg msg = {
                .tx_target_thread = K_ANY,
                .tx_data = &packet,
                .size = sizeof(packet),
                .info = packet.seq,
            };

            int ret = k_mbox_put(&work_mbox, &msg, K_FOREVER);
            if (ret != 0) {
                LOG_ERR("k_mbox_put failed: %d", ret);
            }
        }

        for (int i = 0; i < CONFIG_APP_CLIENT_BURST; ++i) {
            k_sem_take(&done_sem, K_FOREVER);
        }

        const int64_t burst_end_ms = k_uptime_get();
        LOG_INF("client burst seq=%u..%u done in %lld ms (server_prio=%d)",
                burst_start_seq,
                seq - 1,
                burst_end_ms - burst_start_ms,
                CONFIG_APP_SERVER_PRIORITY);

        k_msleep(CONFIG_APP_CLIENT_PAUSE_MS);
    }
}

void main(void) {
    LOG_INF("LAB5 mailbox demo start: server prio=%d client prio=%d burst=%d payload=%d B",
            CONFIG_APP_SERVER_PRIORITY,
            CONFIG_APP_CLIENT_PRIORITY,
            CONFIG_APP_CLIENT_BURST,
            CONFIG_APP_PAYLOAD_BYTES);

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
