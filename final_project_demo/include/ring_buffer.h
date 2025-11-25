#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

typedef struct
{
    uint8_t *buffer;
    size_t entry_size;
    size_t capacity;
    size_t head;
    size_t tail;
    size_t count;
} ring_buffer_t;

bool ring_buffer_init(ring_buffer_t *rb, uint8_t *backing_memory, size_t entry_size, size_t capacity);
bool ring_buffer_push(ring_buffer_t *rb, const void *item);
bool ring_buffer_pop(ring_buffer_t *rb, void *item);
size_t ring_buffer_count(const ring_buffer_t *rb);

#endif /* RING_BUFFER_H */
