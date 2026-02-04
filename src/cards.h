#ifndef CARDS_H
#define CARDS_H

#include <stdint.h>
#include <stddef.h>

#define MAX_CARDS 10000
#define MAX_CARD_NAME_LEN 256

typedef struct {
    uint64_t id;
    char name[MAX_CARD_NAME_LEN];
} Card;

typedef struct {
    Card *cards;
    size_t count;
    size_t capacity;
} CardDb;

/* Initialize card database. Returns 0 on success. */
int carddb_init(CardDb *db);

/* Free card database memory. */
void carddb_free(CardDb *db);

/* Load cards from CSV file. Returns number of cards loaded, -1 on error. */
int carddb_load(CardDb *db, const char *path);

/* Find card by ID. Returns NULL if not found. */
const Card *carddb_find_by_id(CardDb *db, uint64_t id);

/* Find card by name (case-insensitive). Returns NULL if not found. */
const Card *carddb_find_by_name(CardDb *db, const char *name);

/* Get card ID by name. Returns 0 if not found. */
uint64_t carddb_get_id(CardDb *db, const char *name);

/* Get card name by ID. Returns NULL if not found. */
const char *carddb_get_name(CardDb *db, uint64_t id);

/* Add a card to the database (used during loading). */
int carddb_add(CardDb *db, uint64_t id, const char *name);

#endif /* CARDS_H */
