#include "hash.h"
#include <stdlib.h>
#include <string.h>

/* FNV-1a hash function for uint64 */
static uint64_t hash_u64(uint64_t key) {
    uint64_t hash = 14695981039346656037ULL;
    for (int i = 0; i < 8; i++) {
        hash ^= (key >> (i * 8)) & 0xFF;
        hash *= 1099511628211ULL;
    }
    return hash;
}

int hashmap_init(HashMap *map, size_t initial_capacity) {
    if (!map) return -1;

    /* Ensure capacity is power of 2 */
    size_t cap = 16;
    while (cap < initial_capacity) cap *= 2;

    map->entries = calloc(cap, sizeof(HashEntry));
    if (!map->entries) return -1;

    /* Initialize all entries as empty */
    for (size_t i = 0; i < cap; i++) {
        map->entries[i].key = HASH_EMPTY_KEY;
    }

    map->capacity = cap;
    map->size = 0;
    map->tombstones = 0;

    return 0;
}

void hashmap_free(HashMap *map) {
    if (map && map->entries) {
        free(map->entries);
        map->entries = NULL;
        map->capacity = 0;
        map->size = 0;
    }
}

static int hashmap_resize(HashMap *map) {
    size_t old_cap = map->capacity;
    HashEntry *old_entries = map->entries;

    size_t new_cap = old_cap * 2;
    map->entries = calloc(new_cap, sizeof(HashEntry));
    if (!map->entries) {
        map->entries = old_entries;
        return -1;
    }

    for (size_t i = 0; i < new_cap; i++) {
        map->entries[i].key = HASH_EMPTY_KEY;
    }

    map->capacity = new_cap;
    map->size = 0;
    map->tombstones = 0;

    /* Reinsert all entries */
    for (size_t i = 0; i < old_cap; i++) {
        if (old_entries[i].key != HASH_EMPTY_KEY &&
            old_entries[i].key != HASH_TOMBSTONE) {
            HashEntry *entry = hashmap_put(map, old_entries[i].key);
            entry->n = old_entries[i].n;
            entry->w = old_entries[i].w;
        }
    }

    free(old_entries);
    return 0;
}

HashEntry *hashmap_get(HashMap *map, uint64_t key) {
    if (!map || !map->entries || key == HASH_EMPTY_KEY || key == HASH_TOMBSTONE) {
        return NULL;
    }

    uint64_t hash = hash_u64(key);
    size_t mask = map->capacity - 1;
    size_t idx = hash & mask;

    for (size_t i = 0; i < map->capacity; i++) {
        size_t probe = (idx + i) & mask;
        HashEntry *entry = &map->entries[probe];

        if (entry->key == key) {
            return entry;
        }
        if (entry->key == HASH_EMPTY_KEY) {
            return NULL;  /* Not found */
        }
        /* Continue on tombstone */
    }

    return NULL;
}

HashEntry *hashmap_put(HashMap *map, uint64_t key) {
    if (!map || key == HASH_EMPTY_KEY || key == HASH_TOMBSTONE) {
        return NULL;
    }

    /* Resize if load factor > 0.7 */
    if ((map->size + map->tombstones) * 10 > map->capacity * 7) {
        if (hashmap_resize(map) != 0) {
            return NULL;
        }
    }

    uint64_t hash = hash_u64(key);
    size_t mask = map->capacity - 1;
    size_t idx = hash & mask;
    size_t first_tombstone = SIZE_MAX;

    for (size_t i = 0; i < map->capacity; i++) {
        size_t probe = (idx + i) & mask;
        HashEntry *entry = &map->entries[probe];

        if (entry->key == key) {
            return entry;  /* Already exists */
        }
        if (entry->key == HASH_TOMBSTONE && first_tombstone == SIZE_MAX) {
            first_tombstone = probe;
        }
        if (entry->key == HASH_EMPTY_KEY) {
            /* Use tombstone if found, otherwise use empty slot */
            if (first_tombstone != SIZE_MAX) {
                probe = first_tombstone;
                entry = &map->entries[probe];
                map->tombstones--;
            }
            entry->key = key;
            entry->n = 0;
            entry->w = 0;
            map->size++;
            return entry;
        }
    }

    return NULL;  /* Should not reach here */
}

void hashmap_increment(HashMap *map, uint64_t key, int win) {
    HashEntry *entry = hashmap_put(map, key);
    if (entry) {
        entry->n++;
        if (win) entry->w++;
    }
}

void hashmap_iterate(HashMap *map, HashIterator callback, void *ctx) {
    if (!map || !callback) return;

    for (size_t i = 0; i < map->capacity; i++) {
        HashEntry *entry = &map->entries[i];
        if (entry->key != HASH_EMPTY_KEY && entry->key != HASH_TOMBSTONE) {
            callback(entry->key, entry->n, entry->w, ctx);
        }
    }
}

size_t hashmap_size(HashMap *map) {
    return map ? map->size : 0;
}

/* Pair encoding: use Cantor pairing function for unordered pairs */
uint64_t pair_key(uint64_t a, uint64_t b) {
    /* Ensure a <= b for consistent ordering */
    if (a > b) {
        uint64_t tmp = a;
        a = b;
        b = tmp;
    }
    /* Cantor pairing: ((a + b) * (a + b + 1)) / 2 + b */
    /* But we need to handle large numbers, so use a simpler scheme */
    /* Pack two 32-bit values into 64 bits */
    uint32_t a32 = (uint32_t)(a & 0xFFFFFFFF);
    uint32_t b32 = (uint32_t)(b & 0xFFFFFFFF);
    return ((uint64_t)a32 << 32) | (uint64_t)b32;
}

void pair_decode(uint64_t key, uint64_t *a, uint64_t *b) {
    *a = (key >> 32) & 0xFFFFFFFF;
    *b = key & 0xFFFFFFFF;
}
