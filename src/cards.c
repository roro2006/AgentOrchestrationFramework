#include "cards.h"
#include "csv.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

int carddb_init(CardDb *db) {
    if (!db) return -1;

    db->capacity = 1024;
    db->cards = malloc(db->capacity * sizeof(Card));
    if (!db->cards) return -1;

    db->count = 0;
    return 0;
}

void carddb_free(CardDb *db) {
    if (db && db->cards) {
        free(db->cards);
        db->cards = NULL;
        db->count = 0;
        db->capacity = 0;
    }
}

int carddb_add(CardDb *db, uint64_t id, const char *name) {
    if (!db || !name) return -1;

    /* Check if we need to grow */
    if (db->count >= db->capacity) {
        size_t new_cap = db->capacity * 2;
        Card *new_cards = realloc(db->cards, new_cap * sizeof(Card));
        if (!new_cards) return -1;
        db->cards = new_cards;
        db->capacity = new_cap;
    }

    Card *card = &db->cards[db->count];
    card->id = id;
    strncpy(card->name, name, MAX_CARD_NAME_LEN - 1);
    card->name[MAX_CARD_NAME_LEN - 1] = '\0';
    db->count++;

    return 0;
}

int carddb_load(CardDb *db, const char *path) {
    if (!db || !path) return -1;

    CsvReader reader;
    if (csv_open(&reader, path) != 0) {
        return -1;
    }

    /* Read header row */
    if (csv_next_row(&reader) != 1) {
        csv_close(&reader);
        return -1;
    }

    int id_col = csv_find_column(&reader, "id");
    int name_col = csv_find_column(&reader, "name");

    /* If "id" not found, try "mtga_id" */
    if (id_col < 0) {
        id_col = csv_find_column(&reader, "mtga_id");
    }

    if (id_col < 0 || name_col < 0) {
        csv_close(&reader);
        return -1;
    }

    int count = 0;
    while (csv_next_row(&reader) == 1) {
        const char *id_str = csv_get_field(&reader, id_col);
        const char *name = csv_get_field(&reader, name_col);

        if (id_str && name && strlen(name) > 0) {
            uint64_t id = strtoull(id_str, NULL, 10);
            if (id > 0 && carddb_add(db, id, name) == 0) {
                count++;
            }
        }
    }

    csv_close(&reader);
    return count;
}

const Card *carddb_find_by_id(CardDb *db, uint64_t id) {
    if (!db) return NULL;

    for (size_t i = 0; i < db->count; i++) {
        if (db->cards[i].id == id) {
            return &db->cards[i];
        }
    }
    return NULL;
}

/* Case-insensitive string comparison */
static int strcasecmp_custom(const char *a, const char *b) {
    while (*a && *b) {
        int ca = tolower((unsigned char)*a);
        int cb = tolower((unsigned char)*b);
        if (ca != cb) return ca - cb;
        a++;
        b++;
    }
    return tolower((unsigned char)*a) - tolower((unsigned char)*b);
}

const Card *carddb_find_by_name(CardDb *db, const char *name) {
    if (!db || !name) return NULL;

    for (size_t i = 0; i < db->count; i++) {
        if (strcasecmp_custom(db->cards[i].name, name) == 0) {
            return &db->cards[i];
        }
    }
    return NULL;
}

uint64_t carddb_get_id(CardDb *db, const char *name) {
    const Card *card = carddb_find_by_name(db, name);
    return card ? card->id : 0;
}

const char *carddb_get_name(CardDb *db, uint64_t id) {
    const Card *card = carddb_find_by_id(db, id);
    return card ? card->name : NULL;
}
