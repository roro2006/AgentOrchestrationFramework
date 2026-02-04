#ifndef CSV_H
#define CSV_H

#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

#define CSV_MAX_LINE 65536
#define CSV_MAX_FIELDS 4096
#define CSV_MAX_FIELD_LEN 4096

typedef struct {
    FILE *fp;
    char line[CSV_MAX_LINE];
    char *fields[CSV_MAX_FIELDS];
    int num_fields;
    int line_number;
} CsvReader;

/* Initialize CSV reader with file path. Returns 0 on success, -1 on error. */
int csv_open(CsvReader *reader, const char *path);

/* Read next row. Returns 1 if row read, 0 on EOF, -1 on error. */
int csv_next_row(CsvReader *reader);

/* Get field by index (0-based). Returns NULL if out of bounds. */
const char *csv_get_field(CsvReader *reader, int index);

/* Get field index by header name. Call after reading header row. Returns -1 if not found. */
int csv_find_column(CsvReader *reader, const char *name);

/* Close the CSV reader. */
void csv_close(CsvReader *reader);

/* Parse a list field like "[1,2,3]" into an array of uint64. Returns count. */
int csv_parse_list(const char *field, uint64_t *out, int max_count);

#endif /* CSV_H */
