#ifndef HASH_H
#define HASH_H

#include <stdint.h>
#include <stddef.h>

/* Generic hash map with uint64 keys */

#define HASH_EMPTY_KEY  UINT64_MAX
#define HASH_TOMBSTONE  (UINT64_MAX - 1)

/* Hash map entry - stores key and value inline */
typedef struct {
    uint64_t key;
    uint64_t n;      /* count */
    uint64_t w;      /* wins */
} HashEntry;

typedef struct {
    HashEntry *entries;
    size_t capacity;
    size_t size;
    size_t tombstones;
} HashMap;

/* Initialize hash map with given initial capacity. Returns 0 on success. */
int hashmap_init(HashMap *map, size_t initial_capacity);

/* Free hash map memory. */
void hashmap_free(HashMap *map);

/* Get entry for key. Returns NULL if not found. */
HashEntry *hashmap_get(HashMap *map, uint64_t key);

/* Insert or update entry. Returns pointer to entry. */
HashEntry *hashmap_put(HashMap *map, uint64_t key);

/* Increment n and optionally w for a key. Creates entry if needed. */
void hashmap_increment(HashMap *map, uint64_t key, int win);

/* Iterate over all entries. Calls callback for each non-empty entry. */
typedef void (*HashIterator)(uint64_t key, uint64_t n, uint64_t w, void *ctx);
void hashmap_iterate(HashMap *map, HashIterator callback, void *ctx);

/* Get number of entries */
size_t hashmap_size(HashMap *map);

/* --- Pair Hash Map (for storing pair statistics) --- */

/* Combine two card IDs into a single pair key (unordered) */
uint64_t pair_key(uint64_t a, uint64_t b);

/* Extract card IDs from pair key */
void pair_decode(uint64_t key, uint64_t *a, uint64_t *b);

#endif /* HASH_H */
