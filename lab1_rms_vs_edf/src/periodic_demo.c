#if !defined(__linux__)
#error "This example targets Linux with real-time scheduling (SCHED_FIFO/SCHED_DEADLINE)."
#endif

#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>

#ifndef SCHED_DEADLINE
#define SCHED_DEADLINE 6
#endif

#ifndef SYS_sched_setattr
#define SYS_sched_setattr 314
#endif

#ifndef SYS_gettid
#define SYS_gettid 186
#endif

struct sched_attr {
    uint32_t size;
    uint32_t sched_policy;
    uint64_t sched_flags;

    int32_t sched_nice;
    uint32_t sched_priority;

    uint64_t sched_runtime;
    uint64_t sched_deadline;
    uint64_t sched_period;
};

typedef enum {
    POLICY_RMS,
    POLICY_EDF_KERNEL,
    POLICY_EDF_USER
} policy_t;

typedef struct {
    char name[32];
    uint32_t exec_ms;
    uint32_t period_ms;
    uint32_t deadline_ms;
} task_config_t;

typedef struct {
    task_config_t cfg;
    struct timespec next_release;
    uint64_t iteration;
    bool stop;
} task_state_t;

typedef struct {
    policy_t policy;
    double duration_s;
    int cpu_affinity;
    const char *output_path;
} run_opts_t;

static task_state_t *g_states = NULL;
static size_t g_task_count = 0;
static run_opts_t g_opts;
static FILE *g_log_file = NULL;
static pthread_mutex_t g_log_lock = PTHREAD_MUTEX_INITIALIZER;
static struct timespec g_end_time;
static struct timespec g_start_time;
static pthread_mutex_t g_dispatch_lock = PTHREAD_MUTEX_INITIALIZER;

static int64_t timespec_to_ns(const struct timespec *ts) {
    return (int64_t)ts->tv_sec * 1000000000LL + ts->tv_nsec;
}

static struct timespec ns_to_timespec(int64_t ns) {
    struct timespec ts;
    ts.tv_sec = ns / 1000000000LL;
    ts.tv_nsec = ns % 1000000000LL;
    if (ts.tv_nsec < 0) {
        ts.tv_sec -= 1;
        ts.tv_nsec += 1000000000LL;
    }
    return ts;
}

static struct timespec timespec_add_ms(const struct timespec *ts, uint32_t ms) {
    int64_t ns = timespec_to_ns(ts) + (int64_t)ms * 1000000LL;
    return ns_to_timespec(ns);
}

static struct timespec timespec_add_ns(const struct timespec *ts, int64_t ns_delta) {
    int64_t ns = timespec_to_ns(ts) + ns_delta;
    return ns_to_timespec(ns);
}

static int64_t timespec_diff_ns(const struct timespec *a, const struct timespec *b) {
    return timespec_to_ns(a) - timespec_to_ns(b);
}

static void busy_spin_until(const struct timespec *deadline) {
    struct timespec now;
    do {
        clock_gettime(CLOCK_MONOTONIC, &now);
    } while (timespec_diff_ns(deadline, &now) > 0);
}

static int set_fifo_priority(int prio) {
    struct sched_param sp = {0};
    sp.sched_priority = prio;
    return pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp);
}

static int set_deadline(uint64_t runtime_ns, uint64_t deadline_ns, uint64_t period_ns) {
    struct sched_attr attr = {
        .size = sizeof(struct sched_attr),
        .sched_policy = SCHED_DEADLINE,
        .sched_flags = 0,
        .sched_nice = 0,
        .sched_priority = 0,
        .sched_runtime = runtime_ns,
        .sched_deadline = deadline_ns,
        .sched_period = period_ns,
    };

    pid_t tid = (pid_t)syscall(SYS_gettid);
    return syscall(SYS_sched_setattr, tid, &attr, 0);
}

static void log_result(const char *task_name,
                       uint64_t iteration,
                       int deadline_hit,
                       int64_t latency_us,
                       int64_t runtime_us,
                       const struct timespec *timestamp) {
    int64_t ts_ns = timespec_to_ns(timestamp);
    pthread_mutex_lock(&g_log_lock);
    if (g_log_file) {
        fprintf(g_log_file, "%lld,%s,%llu,%d,%lld,%lld\n",
                (long long)ts_ns,
                task_name,
                (unsigned long long)iteration,
                deadline_hit,
                (long long)latency_us,
                (long long)runtime_us);
        fflush(g_log_file);
    }
    pthread_mutex_unlock(&g_log_lock);
}

static int compare_period(const void *lhs, const void *rhs) {
    const task_config_t *a = lhs;
    const task_config_t *b = rhs;
    if (a->period_ms < b->period_ms) return -1;
    if (a->period_ms > b->period_ms) return 1;
    return strcmp(a->name, b->name);
}

typedef struct {
    task_state_t *state;
    int fifo_priority;
} thread_arg_t;

static void apply_user_edf_priority(task_state_t *self, const struct timespec *absolute_deadline) {
    (void)absolute_deadline;
    /* Simple heuristic: adjust FIFO priority based on the next iteration count */
    int desired = 80 - (int)(self->iteration % 5);
    if (desired < 10) desired = 10;
    set_fifo_priority(desired);
}

static void *task_entry(void *arg) {
    thread_arg_t *thread_arg = (thread_arg_t *)arg;
    task_state_t *state = thread_arg->state;
    task_config_t *cfg = &state->cfg;
    const uint64_t exec_ns = (uint64_t)cfg->exec_ms * 1000000ULL;
    const uint64_t period_ns = (uint64_t)cfg->period_ms * 1000000ULL;
    const uint64_t deadline_ns = (uint64_t)cfg->deadline_ms * 1000000ULL;

    if (g_opts.cpu_affinity >= 0) {
        cpu_set_t set;
        CPU_ZERO(&set);
        CPU_SET(g_opts.cpu_affinity, &set);
        if (pthread_setaffinity_np(pthread_self(), sizeof(set), &set) != 0) {
            perror("pthread_setaffinity_np");
        }
    }

    if (g_opts.policy == POLICY_RMS) {
        if (set_fifo_priority(thread_arg->fifo_priority) != 0) {
            perror("pthread_setschedparam(SCHED_FIFO)");
        }
    } else if (g_opts.policy == POLICY_EDF_KERNEL) {
        if (set_deadline(exec_ns, deadline_ns, period_ns) != 0) {
            perror("sched_setattr(SCHED_DEADLINE)");
            fprintf(stderr, "Falling back to SCHED_FIFO for %s\n", cfg->name);
            set_fifo_priority(thread_arg->fifo_priority);
        }
    } else {
        if (set_fifo_priority(thread_arg->fifo_priority) != 0) {
            perror("pthread_setschedparam(SCHED_FIFO)");
        }
    }

    pthread_setname_np(pthread_self(), cfg->name);

    while (!state->stop) {
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &state->next_release, NULL);

        struct timespec start;
        clock_gettime(CLOCK_MONOTONIC, &start);

        struct timespec expected_release = state->next_release;
        struct timespec abs_deadline = timespec_add_ns(&expected_release, deadline_ns);

        if (g_opts.policy == POLICY_EDF_USER) {
            pthread_mutex_lock(&g_dispatch_lock);
            apply_user_edf_priority(state, &abs_deadline);
            pthread_mutex_unlock(&g_dispatch_lock);
        }

        struct timespec work_until = timespec_add_ns(&start, exec_ns);
        busy_spin_until(&work_until);

        struct timespec finish;
        clock_gettime(CLOCK_MONOTONIC, &finish);

        int64_t latency_us = timespec_diff_ns(&start, &expected_release) / 1000LL;
        int64_t runtime_us = timespec_diff_ns(&finish, &start) / 1000LL;
        int deadline_hit = timespec_diff_ns(&abs_deadline, &finish) >= 0 ? 1 : 0;

        log_result(cfg->name,
                   state->iteration,
                   deadline_hit,
                   latency_us,
                   runtime_us,
                   &start);

        state->iteration++;
        state->next_release = timespec_add_ms(&state->next_release, cfg->period_ms);

        struct timespec now;
        clock_gettime(CLOCK_MONOTONIC, &now);
        if (timespec_diff_ns(&g_end_time, &now) <= 0) {
            break;
        }
    }

    return NULL;
}

static int parse_task(const char *arg, task_config_t *out) {
    char buffer[128];
    strncpy(buffer, arg, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char *token;
    char *save = NULL;
    token = strtok_r(buffer, ",", &save);
    while (token) {
        char *eq = strchr(token, '=');
        if (!eq) return -1;
        *eq = '\0';
        const char *key = token;
        const char *value = eq + 1;

        if (strcmp(key, "name") == 0) {
            strncpy(out->name, value, sizeof(out->name) - 1);
            out->name[sizeof(out->name) - 1] = '\0';
        } else if (strcmp(key, "exec_ms") == 0) {
            out->exec_ms = (uint32_t)strtoul(value, NULL, 10);
        } else if (strcmp(key, "period_ms") == 0) {
            out->period_ms = (uint32_t)strtoul(value, NULL, 10);
        } else if (strcmp(key, "deadline_ms") == 0) {
            out->deadline_ms = (uint32_t)strtoul(value, NULL, 10);
        } else {
            return -1;
        }
        token = strtok_r(NULL, ",", &save);
    }

    if (out->name[0] == '\0' || out->period_ms == 0 || out->deadline_ms == 0 || out->exec_ms == 0) {
        return -1;
    }
    return 0;
}

static void usage(const char *prog) {
    fprintf(stderr,
            "Usage: %s --policy [rms|edf|edf-userspace] --task name=...,exec_ms=...,period_ms=...,deadline_ms=... [--duration SEC] [--cpu N] [--output file]\n",
            prog);
}

int main(int argc, char **argv) {
    memset(&g_opts, 0, sizeof(g_opts));
    g_opts.duration_s = 20.0;
    g_opts.cpu_affinity = -1;
    g_opts.output_path = "schedule_log.csv";

    task_config_t configs[16];
    size_t config_count = 0;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--policy") == 0 && i + 1 < argc) {
            ++i;
            if (strcmp(argv[i], "rms") == 0) {
                g_opts.policy = POLICY_RMS;
            } else if (strcmp(argv[i], "edf") == 0) {
                g_opts.policy = POLICY_EDF_KERNEL;
            } else if (strcmp(argv[i], "edf-userspace") == 0) {
                g_opts.policy = POLICY_EDF_USER;
            } else {
                fprintf(stderr, "Unknown policy: %s\n", argv[i]);
                return EXIT_FAILURE;
            }
        } else if (strcmp(argv[i], "--task") == 0 && i + 1 < argc) {
            if (config_count >= 16) {
                fprintf(stderr, "Too many tasks (max 16).\n");
                return EXIT_FAILURE;
            }
            if (parse_task(argv[++i], &configs[config_count]) != 0) {
                fprintf(stderr, "Failed to parse task: %s\n", argv[i]);
                return EXIT_FAILURE;
            }
            ++config_count;
        } else if (strcmp(argv[i], "--duration") == 0 && i + 1 < argc) {
            g_opts.duration_s = atof(argv[++i]);
        } else if (strcmp(argv[i], "--cpu") == 0 && i + 1 < argc) {
            g_opts.cpu_affinity = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--output") == 0 && i + 1 < argc) {
            g_opts.output_path = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            return EXIT_SUCCESS;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", argv[i]);
            usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    if (config_count == 0) {
        fprintf(stderr, "At least one --task is required.\n");
        return EXIT_FAILURE;
    }

    if (g_opts.policy == POLICY_RMS) {
        qsort(configs, config_count, sizeof(task_config_t), compare_period);
    }

    g_log_file = fopen(g_opts.output_path, "w");
    if (!g_log_file) {
        perror("fopen");
        return EXIT_FAILURE;
    }
    fprintf(g_log_file, "start_ns,task,iteration,deadline_hit,latency_us,runtime_us\n");

    g_task_count = config_count;
    g_states = calloc(g_task_count, sizeof(task_state_t));
    if (!g_states) {
        perror("calloc");
        return EXIT_FAILURE;
    }

    clock_gettime(CLOCK_MONOTONIC, &g_start_time);
    g_end_time = timespec_add_ns(&g_start_time, (int64_t)(g_opts.duration_s * 1e9));

    pthread_t threads[16];
    thread_arg_t thread_args[16];

    for (size_t i = 0; i < g_task_count; ++i) {
        g_states[i].cfg = configs[i];
        g_states[i].iteration = 0;
        g_states[i].next_release = g_start_time;
        g_states[i].stop = false;

        thread_args[i].state = &g_states[i];
        thread_args[i].fifo_priority = 80 - (int)i * 2;
        if (thread_args[i].fifo_priority < 10) {
            thread_args[i].fifo_priority = 10;
        }

        int rc = pthread_create(&threads[i], NULL, task_entry, &thread_args[i]);
        if (rc != 0) {
            errno = rc;
            perror("pthread_create");
            return EXIT_FAILURE;
        }
        usleep(1000);
    }

    for (size_t i = 0; i < g_task_count; ++i) {
        pthread_join(threads[i], NULL);
    }

    fclose(g_log_file);
    free(g_states);

    return EXIT_SUCCESS;
}
