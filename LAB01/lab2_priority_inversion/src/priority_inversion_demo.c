#define _GNU_SOURCE
#define _POSIX_C_SOURCE 200809L

#if !defined(__linux__)
#error "Bài lab này yêu cầu chạy trên Linux với hỗ trợ SCHED_FIFO."
#endif

#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

typedef enum {
    PI_NONE,
    PI_INHERIT
} pi_mode_t;

typedef struct {
    int iterations;
    int hold_ms;
    int meddler_ms;
    int critical_ms;
    int cpu_affinity;
    pi_mode_t mode;
    const char *output_path;
} config_t;

typedef struct {
    pthread_mutex_t test_mutex;
    pthread_barrier_t start_barrier;
    pthread_barrier_t lock_barrier;
    pthread_barrier_t end_barrier;
    config_t cfg;
    double *responses_ms;
} experiment_t;

typedef struct {
    experiment_t *exp;
    const char *name;
    int priority;
} thread_arg_t;

static inline int64_t timespec_to_ns(const struct timespec *ts) {
    return (int64_t)ts->tv_sec * 1000000000LL + ts->tv_nsec;
}

static inline void busy_spin_for_ms(int ms) {
    const int64_t duration_ns = (int64_t)ms * 1000000LL;
    struct timespec start;
    clock_gettime(CLOCK_MONOTONIC, &start);
    const int64_t deadline_ns = timespec_to_ns(&start) + duration_ns;
    struct timespec now;
    do {
        clock_gettime(CLOCK_MONOTONIC, &now);
    } while (timespec_to_ns(&now) < deadline_ns);
}

static void set_thread_priority(int prio) {
    struct sched_param sp = {0};
    sp.sched_priority = prio;
    if (pthread_setschedparam(pthread_self(), SCHED_FIFO, &sp) != 0) {
        perror("pthread_setschedparam");
    }
}

static void *low_thread(void *arg) {
    thread_arg_t *targ = arg;
    experiment_t *exp = targ->exp;

    if (targ->priority > 0) {
        set_thread_priority(targ->priority);
    }
    pthread_setname_np(pthread_self(), "low");

    if (exp->cfg.cpu_affinity >= 0) {
        cpu_set_t set;
        CPU_ZERO(&set);
        CPU_SET(exp->cfg.cpu_affinity, &set);
        if (pthread_setaffinity_np(pthread_self(), sizeof(set), &set) != 0) {
            perror("pthread_setaffinity_np");
        }
    }

    for (int i = 0; i < exp->cfg.iterations; ++i) {
        pthread_barrier_wait(&exp->start_barrier);

        pthread_mutex_lock(&exp->test_mutex);
        pthread_barrier_wait(&exp->lock_barrier);
        busy_spin_for_ms(exp->cfg.hold_ms);
        pthread_mutex_unlock(&exp->test_mutex);

        pthread_barrier_wait(&exp->end_barrier);
    }

    return NULL;
}

static void *medium_thread(void *arg) {
    thread_arg_t *targ = arg;
    experiment_t *exp = targ->exp;

    if (targ->priority > 0) {
        set_thread_priority(targ->priority);
    }
    pthread_setname_np(pthread_self(), "medium");

    if (exp->cfg.cpu_affinity >= 0) {
        cpu_set_t set;
        CPU_ZERO(&set);
        CPU_SET(exp->cfg.cpu_affinity, &set);
        if (pthread_setaffinity_np(pthread_self(), sizeof(set), &set) != 0) {
            perror("pthread_setaffinity_np");
        }
    }

    for (int i = 0; i < exp->cfg.iterations; ++i) {
        pthread_barrier_wait(&exp->start_barrier);

        busy_spin_for_ms(exp->cfg.meddler_ms);

        pthread_barrier_wait(&exp->end_barrier);
    }

    return NULL;
}

static void *high_thread(void *arg) {
    thread_arg_t *targ = arg;
    experiment_t *exp = targ->exp;

    if (targ->priority > 0) {
        set_thread_priority(targ->priority);
    }
    pthread_setname_np(pthread_self(), "high");

    if (exp->cfg.cpu_affinity >= 0) {
        cpu_set_t set;
        CPU_ZERO(&set);
        CPU_SET(exp->cfg.cpu_affinity, &set);
        if (pthread_setaffinity_np(pthread_self(), sizeof(set), &set) != 0) {
            perror("pthread_setaffinity_np");
        }
    }

    for (int i = 0; i < exp->cfg.iterations; ++i) {
        pthread_barrier_wait(&exp->start_barrier);

        pthread_barrier_wait(&exp->lock_barrier);

        struct timespec start, acquired, finish;
        clock_gettime(CLOCK_MONOTONIC, &start);
        pthread_mutex_lock(&exp->test_mutex);
        clock_gettime(CLOCK_MONOTONIC, &acquired);
        busy_spin_for_ms(exp->cfg.critical_ms);
        pthread_mutex_unlock(&exp->test_mutex);
        clock_gettime(CLOCK_MONOTONIC, &finish);

        double response_ms = (timespec_to_ns(&finish) - timespec_to_ns(&start)) / 1e6;
        exp->responses_ms[i] = response_ms;

        pthread_barrier_wait(&exp->end_barrier);
    }

    return NULL;
}

static void print_usage(const char *prog) {
    fprintf(stderr,
            "Usage: %s --policy [none|inherit] [--iterations N] [--work-ms N] [--critical-ms N] [--cpu ID] [--output file]\n",
            prog);
}

int main(int argc, char **argv) {
    config_t cfg = {
        .iterations = 20,
        .hold_ms = 100,
        .meddler_ms = 200,
        .critical_ms = 5,
        .cpu_affinity = -1,
        .mode = PI_NONE,
        .output_path = "results.csv",
    };

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--policy") == 0 && i + 1 < argc) {
            ++i;
            if (strcmp(argv[i], "none") == 0) {
                cfg.mode = PI_NONE;
            } else if (strcmp(argv[i], "inherit") == 0) {
                cfg.mode = PI_INHERIT;
            } else {
                fprintf(stderr, "Unknown policy: %s\n", argv[i]);
                return EXIT_FAILURE;
            }
        } else if (strcmp(argv[i], "--iterations") == 0 && i + 1 < argc) {
            cfg.iterations = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--work-ms") == 0 && i + 1 < argc) {
            cfg.meddler_ms = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--hold-ms") == 0 && i + 1 < argc) {
            cfg.hold_ms = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--critical-ms") == 0 && i + 1 < argc) {
            cfg.critical_ms = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--cpu") == 0 && i + 1 < argc) {
            cfg.cpu_affinity = atoi(argv[++i]);
        } else if (strcmp(argv[i], "--output") == 0 && i + 1 < argc) {
            cfg.output_path = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return EXIT_SUCCESS;
        } else {
            fprintf(stderr, "Unknown argument: %s\n", argv[i]);
            print_usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    if (cfg.iterations <= 0) {
        fprintf(stderr, "iterations phải > 0\n");
        return EXIT_FAILURE;
    }

    pthread_mutexattr_t mattr;
    pthread_mutexattr_init(&mattr);
    if (cfg.mode == PI_INHERIT) {
        pthread_mutexattr_setprotocol(&mattr, PTHREAD_PRIO_INHERIT);
    } else {
        pthread_mutexattr_setprotocol(&mattr, PTHREAD_PRIO_NONE);
    }

    experiment_t exp;
    memset(&exp, 0, sizeof(exp));
    exp.cfg = cfg;
    exp.responses_ms = calloc(cfg.iterations, sizeof(double));
    if (!exp.responses_ms) {
        perror("calloc");
        return EXIT_FAILURE;
    }

    pthread_mutex_init(&exp.test_mutex, &mattr);
    pthread_barrier_init(&exp.start_barrier, NULL, 3);
    pthread_barrier_init(&exp.lock_barrier, NULL, 2);
    pthread_barrier_init(&exp.end_barrier, NULL, 3);

    pthread_t threads[3];
    thread_arg_t args[3] = {
        {.exp = &exp, .name = "L", .priority = 10},
        {.exp = &exp, .name = "M", .priority = 60},
        {.exp = &exp, .name = "H", .priority = 90},
    };

    pthread_create(&threads[0], NULL, low_thread, &args[0]);
    pthread_create(&threads[1], NULL, medium_thread, &args[1]);
    pthread_create(&threads[2], NULL, high_thread, &args[2]);

    for (size_t i = 0; i < 3; ++i) {
        pthread_join(threads[i], NULL);
    }

    FILE *f = fopen(cfg.output_path, "w");
    if (!f) {
        perror("fopen");
        return EXIT_FAILURE;
    }
    fprintf(f, "iteration,policy,response_ms\n");
    const char *policy_name = cfg.mode == PI_INHERIT ? "inherit" : "none";
    for (int i = 0; i < cfg.iterations; ++i) {
        fprintf(f, "%d,%s,%.3f\n", i, policy_name, exp.responses_ms[i]);
    }
    fclose(f);

    printf("Saved %d samples to %s (policy=%s)\n", cfg.iterations, cfg.output_path, policy_name);

    free(exp.responses_ms);
    pthread_mutex_destroy(&exp.test_mutex);
    pthread_barrier_destroy(&exp.start_barrier);
    pthread_barrier_destroy(&exp.lock_barrier);
    pthread_barrier_destroy(&exp.end_barrier);

    return EXIT_SUCCESS;
}
