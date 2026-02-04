#include "csv.h"
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <ctype.h>

int csv_open(CsvReader *reader, const char *path) {
    if (!reader || !path) return -1;

    reader->fp = fopen(path, "r");
    if (!reader->fp) return -1;

    reader->num_fields = 0;
    reader->line_number = 0;
    memset(reader->line, 0, sizeof(reader->line));

    return 0;
}

/* Parse a single CSV line, handling quoted fields */
static int parse_csv_line(CsvReader *reader) {
    char *p = reader->line;
    int field_idx = 0;

    while (*p && field_idx < CSV_MAX_FIELDS) {
        reader->fields[field_idx] = p;

        if (*p == '"') {
            /* Quoted field */
            p++;
            reader->fields[field_idx] = p;
            while (*p) {
                if (*p == '"') {
                    if (*(p + 1) == '"') {
                        /* Escaped quote - shift string left */
                        memmove(p, p + 1, strlen(p));
                    } else {
                        /* End of quoted field */
                        *p = '\0';
                        p++;
                        break;
                    }
                }
                p++;
            }
            /* Skip to comma or end */
            while (*p && *p != ',') p++;
            if (*p == ',') {
                p++;
            }
        } else {
            /* Unquoted field */
            while (*p && *p != ',') p++;
            if (*p == ',') {
                *p = '\0';
                p++;
            }
        }
        field_idx++;
    }

    reader->num_fields = field_idx;
    return field_idx;
}

int csv_next_row(CsvReader *reader) {
    if (!reader || !reader->fp) return -1;

    if (!fgets(reader->line, CSV_MAX_LINE, reader->fp)) {
        return 0;  /* EOF */
    }

    reader->line_number++;

    /* Remove trailing newline/carriage return */
    size_t len = strlen(reader->line);
    while (len > 0 && (reader->line[len-1] == '\n' || reader->line[len-1] == '\r')) {
        reader->line[--len] = '\0';
    }

    parse_csv_line(reader);
    return 1;
}

const char *csv_get_field(CsvReader *reader, int index) {
    if (!reader || index < 0 || index >= reader->num_fields) {
        return NULL;
    }
    return reader->fields[index];
}

int csv_find_column(CsvReader *reader, const char *name) {
    if (!reader || !name) return -1;

    for (int i = 0; i < reader->num_fields; i++) {
        if (reader->fields[i] && strcmp(reader->fields[i], name) == 0) {
            return i;
        }
    }
    return -1;
}

void csv_close(CsvReader *reader) {
    if (reader && reader->fp) {
        fclose(reader->fp);
        reader->fp = NULL;
    }
}

int csv_parse_list(const char *field, uint64_t *out, int max_count) {
    if (!field || !out || max_count <= 0) return 0;

    int count = 0;
    const char *p = field;

    /* Skip leading whitespace and bracket */
    while (*p && (isspace((unsigned char)*p) || *p == '[')) p++;

    while (*p && count < max_count) {
        /* Skip whitespace */
        while (*p && isspace((unsigned char)*p)) p++;

        if (*p == ']' || *p == '\0') break;

        /* Parse number */
        if (isdigit((unsigned char)*p)) {
            char *end;
            uint64_t val = strtoull(p, &end, 10);
            out[count++] = val;
            p = end;
        } else {
            p++;
        }

        /* Skip comma and whitespace */
        while (*p && (*p == ',' || isspace((unsigned char)*p))) p++;
    }

    return count;
}
