# 17Lands Card Synergy Project
# Makefile for building all components

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c11
LDFLAGS = -lm

SRC_DIR = src
OBJ_DIR = obj

# Source files
CSV_SRC = $(SRC_DIR)/csv.c
HASH_SRC = $(SRC_DIR)/hash.c
CARDS_SRC = $(SRC_DIR)/cards.c
LABELS_SRC = $(SRC_DIR)/labels.c
TRAIN_SRC = $(SRC_DIR)/train.c

# Common objects
COMMON_OBJS = $(OBJ_DIR)/csv.o $(OBJ_DIR)/hash.o $(OBJ_DIR)/cards.o

# Executables
LABELS_BIN = main_labels
TRAIN_BIN = main_train
INFER_BIN = infer

.PHONY: all clean dirs labels train infer-bin download-data run-all test-infer

all: dirs $(LABELS_BIN) $(TRAIN_BIN) $(INFER_BIN)

dirs:
	@mkdir -p $(OBJ_DIR)
	@mkdir -p data/raw data/tmp data/out

# Object files
$(OBJ_DIR)/csv.o: $(SRC_DIR)/csv.c $(SRC_DIR)/csv.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/hash.o: $(SRC_DIR)/hash.c $(SRC_DIR)/hash.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/cards.o: $(SRC_DIR)/cards.c $(SRC_DIR)/cards.h $(SRC_DIR)/csv.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/labels.o: $(SRC_DIR)/labels.c $(SRC_DIR)/labels.h $(SRC_DIR)/hash.h $(SRC_DIR)/csv.h $(SRC_DIR)/cards.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/train.o: $(SRC_DIR)/train.c $(SRC_DIR)/train.h $(SRC_DIR)/csv.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/main_labels.o: $(SRC_DIR)/main_labels.c $(SRC_DIR)/labels.h $(SRC_DIR)/cards.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/main_train.o: $(SRC_DIR)/main_train.c $(SRC_DIR)/train.h
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/infer.o: $(SRC_DIR)/infer.c $(SRC_DIR)/train.h $(SRC_DIR)/cards.h
	$(CC) $(CFLAGS) -c $< -o $@

# Executables
$(LABELS_BIN): $(COMMON_OBJS) $(OBJ_DIR)/labels.o $(OBJ_DIR)/main_labels.o
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

$(TRAIN_BIN): $(COMMON_OBJS) $(OBJ_DIR)/train.o $(OBJ_DIR)/main_train.o
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

$(INFER_BIN): $(COMMON_OBJS) $(OBJ_DIR)/train.o $(OBJ_DIR)/infer.o
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

clean:
	rm -rf $(OBJ_DIR)
	rm -f $(LABELS_BIN) $(TRAIN_BIN) $(INFER_BIN)

# Convenience targets
labels: $(LABELS_BIN)
train: $(TRAIN_BIN)
infer-bin: $(INFER_BIN)

# Data download (requires curl)
download-data:
	@echo "Downloading 17Lands public data..."
	mkdir -p data/raw data/tmp data/out
	curl -L -o data/raw/powered_premier_games.csv.gz \
		"https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.PremierDraft.csv.gz"
	curl -L -o data/raw/powered_trad_games.csv.gz \
		"https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.Cube_-_Powered.TradDraft.csv.gz"
	curl -L -o data/raw/cards.csv \
		"https://17lands-public.s3.amazonaws.com/analysis_data/cards/cards.csv"
	gunzip -c data/raw/powered_premier_games.csv.gz > data/tmp/powered_premier_games.csv
	gunzip -c data/raw/powered_trad_games.csv.gz > data/tmp/powered_trad_games.csv
	@echo "Data download complete!"

# Full pipeline
run-all: all
	./$(LABELS_BIN) data/tmp/powered_premier_games.csv data/raw/cards.csv data/out/labels_premier.csv
	./$(LABELS_BIN) data/tmp/powered_trad_games.csv data/raw/cards.csv data/out/labels_trad.csv
	./$(TRAIN_BIN) data/out/labels_premier.csv data/out/model_premier.bin
	./$(TRAIN_BIN) data/out/labels_trad.csv data/out/model_trad.bin
	@echo "Pipeline complete!"

# Test inference with known combos
test-infer: $(INFER_BIN)
	@echo "Testing inference..."
	./$(INFER_BIN) data/out/model_premier.bin data/raw/cards.csv "Tinker" "Blightsteel Colossus" || true
	./$(INFER_BIN) data/out/model_premier.bin data/raw/cards.csv "Black Lotus" "Channel" || true
	./$(INFER_BIN) data/out/model_premier.bin data/raw/cards.csv "Time Walk" "Snapcaster Mage" || true
