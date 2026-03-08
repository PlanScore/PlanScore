# Makefile for generating state legislative district combined CSV files
# Uses PlanScore API to score districts and combine results

SHELL := /bin/bash

# Find all zip files
SLDU_ZIPS := $(wildcard SLDU/*.zip)
SLDL_ZIPS := $(wildcard SLDL/*.zip)

# Scripts and specs
SCRIPTS := upload_plans.py combine_results.py preprocess_plan.py process_state_plans.sh
SPECS := SLDU_columns.txt SLDL_columns.txt

.PHONY: all clean test help

all: SLDU_combined.csv SLDL_combined.csv

test: SLDU_combined-test.csv SLDL_combined-test.csv

help:
	@echo "Available targets:"
	@echo "  all                    - Build both SLDU_combined.csv and SLDL_combined.csv (all states)"
	@echo "  test                   - Build test versions (3 states only)"
	@echo "  SLDU_combined.csv      - Build upper chamber combined CSV (all states)"
	@echo "  SLDL_combined.csv      - Build lower chamber combined CSV (all states)"
	@echo "  SLDU_combined-test.csv - Build upper chamber test CSV (3 states)"
	@echo "  SLDL_combined-test.csv - Build lower chamber test CSV (3 states)"
	@echo "  clean                  - Remove generated files and temp directories"

# Full SLDU build
SLDU_combined.csv: $(SLDU_ZIPS) $(SCRIPTS) $(SPECS)
	@echo "Building SLDU_combined.csv (all states)..."
	./process_state_plans.sh SLDU

# Full SLDL build
SLDL_combined.csv: $(SLDL_ZIPS) $(SCRIPTS) $(SPECS)
	@echo "Building SLDL_combined.csv (all states)..."
	./process_state_plans.sh SLDL

# Test SLDU build (3 states only)
SLDU_combined-test.csv: $(SLDU_ZIPS) $(SCRIPTS) $(SPECS)
	@echo "Building SLDU_combined-test.csv (3 states)..."
	./process_state_plans.sh SLDU test
	mv SLDU_combined.csv SLDU_combined-test.csv

# Test SLDL build (3 states only)
SLDL_combined-test.csv: $(SLDL_ZIPS) $(SCRIPTS) $(SPECS)
	@echo "Building SLDL_combined-test.csv (3 states)..."
	./process_state_plans.sh SLDL test
	mv SLDL_combined.csv SLDL_combined-test.csv

clean:
	@echo "Cleaning generated files and temp directories..."
	@rm -f SLDU_combined.csv SLDL_combined.csv
	@rm -f SLDU_combined-test.csv SLDL_combined-test.csv
	@rm -rf SLDU_results SLDL_results
	@rm -rf SLDU-ordered SLDL-ordered
	@echo "✓ Cleaned"
