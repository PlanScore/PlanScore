#!/bin/bash
# Process state legislative district plans through PlanScore API
# Usage: process_state_plans.sh <SLDL|SLDU> [test]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DISTRICT_TYPE=$1
TEST_MODE=$2

if [ "$DISTRICT_TYPE" != "SLDL" ] && [ "$DISTRICT_TYPE" != "SLDU" ]; then
    echo "Usage: $0 <SLDL|SLDU> [test]"
    echo "  SLDL: State Legislative Lower Districts"
    echo "  SLDU: State Legislative Upper Districts"
    echo "  test: Optional - process only 3 states for testing"
    exit 1
fi

INPUT_DIR="$SCRIPT_DIR/$DISTRICT_TYPE"
OUTPUT_DIR="$SCRIPT_DIR/${DISTRICT_TYPE}_results"
ORDERED_DIR="$SCRIPT_DIR/${DISTRICT_TYPE}-ordered"
FINAL_CSV="$SCRIPT_DIR/${DISTRICT_TYPE}_combined.csv"
COLUMN_SPEC="$SCRIPT_DIR/${DISTRICT_TYPE}_columns.txt"

echo "Processing $DISTRICT_TYPE districts..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

# Get list of zip files
if [ "$TEST_MODE" == "test" ]; then
    echo "TEST MODE: Processing only 3 states"
    ZIP_FILES=$(ls -1 "$INPUT_DIR"/*.zip | head -3)
else
    echo "FULL MODE: Processing all states"
    ZIP_FILES=$(ls -1 "$INPUT_DIR"/*.zip)
fi

# Create ordered directory
mkdir -p "$ORDERED_DIR"

# Upload plans and retrieve results
python3 "$SCRIPT_DIR/upload_plans.py" "$OUTPUT_DIR" "$ORDERED_DIR" $ZIP_FILES

# Combine results with column specification
python3 "$SCRIPT_DIR/combine_results.py" "$OUTPUT_DIR/manifest.json" "$FINAL_CSV" "$COLUMN_SPEC"

echo ""
echo "==============================================="
echo "Process complete!"
echo "Individual results: $OUTPUT_DIR"
echo "Combined CSV: $FINAL_CSV"
echo "==============================================="
