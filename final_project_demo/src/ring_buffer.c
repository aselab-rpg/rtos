#include "ring_buffer.h"

#include <string.h>

bool ring_buffer_init(ring_buffer_t *rb, uint8_t *backing_memory, size_t entry_size, size_t capacity)
{
    if ((rb == NULL) || (backing_memory == NULL) || (entry_size == 0U) || (capacity == 0U))
    {
        return false;
    }

    rb->buffer = backing_memory;
    rb->entry_size = entry_size;
    rb->capacity = capacity;
    rb->head = 0U;
    rb->tail = 0U;
    rb->count = 0U;
    return true;
}

bool ring_buffer_push(ring_buffer_t *rb, const void *item)
{
    if ((rb == NULL) || (item == NULL) || (rb->count == rb->capacity))
    {
        return false;
    }

    uint8_t *destination = rb->buffer + (rb->head * rb->entry_size);
    memcpy(destination, item, rb->entry_size);

    rb->head = (rb->head + 1U) % rb->capacity;
    rb->count++;
    return true;
}

bool ring_buffer_pop(ring_buffer_t *rb, void *item)
{
    if ((rb == NULL) || (item == NULL) || (rb->count == 0U))
    {
        return false;
    }

    const uint8_t *source = rb->buffer + (rb->tail * rb->entry_size);
    memcpy(item, source, rb->entry_size);

    rb->tail = (rb->tail + 1U) % rb->capacity;
    rb->count--;
    return true;
}

size_t ring_buffer_count(const ring_buffer_t *rb)
{
    return (rb != NULL) ? rb->count : 0U;
}
