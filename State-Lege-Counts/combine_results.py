#!/usr/bin/env python3
"""
Combine index.txt files into a single CSV with columns matching specifications.
"""
import json
import sys
import os
import csv
import tempfile
import subprocess
import shutil


def read_column_spec(spec_file):
    """Read column specification from tab-delimited file."""
    with open(spec_file, 'r') as f:
        header = f.readline().strip()
        columns = header.split('\t')
    return columns


def map_column_name(original_name):
    """Map original column names to specification names."""
    # Handle special mappings
    mapping = {
        'state': 'State',
        'filename': 'Filename',
        'plan_url': 'Plan URL',
        'district': 'District',
        'District': 'District',  # Already correct
    }

    # Check if it's in our mapping
    if original_name.lower() in [k.lower() for k in mapping.keys()]:
        for k, v in mapping.items():
            if k.lower() == original_name.lower():
                return v

    # Otherwise return as-is
    return original_name


def main():
    if len(sys.argv) < 4:
        print("Usage: combine_results.py <manifest.json> <output.csv> <spec_file>")
        sys.exit(1)

    manifest_path = sys.argv[1]
    output_csv = sys.argv[2]
    spec_file = sys.argv[3]

    # Load column specification
    if not os.path.exists(spec_file):
        print(f"ERROR: Column specification file not found: {spec_file}")
        sys.exit(1)

    target_columns = read_column_spec(spec_file)
    print(f"Target columns from {spec_file}: {len(target_columns)} columns")

    # Load manifest
    with open(manifest_path) as f:
        results = json.load(f)

    # Filter successful results
    successful = [r for r in results if r["success"] and r["file"]]

    if not successful:
        print("No successful results to combine")
        sys.exit(1)

    print(f"Combining {len(successful)} files...")

    # Create temporary files with added and reordered columns
    temp_files = []
    temp_dir = tempfile.mkdtemp()

    try:
        for result in successful:
            state = result["state"]
            filename = result["filename"]
            plan_url = result.get("plan_url", "")
            input_file = result["file"]

            # Create temp file with added columns
            temp_file = os.path.join(temp_dir, os.path.basename(input_file))
            temp_files.append(temp_file)

            with open(input_file, 'r') as infile, open(temp_file, 'w', newline='') as outfile:
                reader = csv.DictReader(infile, delimiter='\t')
                writer = csv.DictWriter(outfile, fieldnames=target_columns, delimiter='\t', extrasaction='ignore')

                writer.writeheader()

                # Process data rows
                for row in reader:
                    # Add our metadata columns
                    row['State'] = state
                    row['Filename'] = filename
                    row['Plan URL'] = plan_url

                    # Map any column name variations
                    mapped_row = {}
                    for key, value in row.items():
                        mapped_key = map_column_name(key)
                        mapped_row[mapped_key] = value

                    # Ensure all target columns exist (fill missing with empty string)
                    output_row = {col: mapped_row.get(col, '') for col in target_columns}

                    writer.writerow(output_row)

        # Now use csvstack to combine them
        cmd = ["csvstack", "-t"] + temp_files

        print(f"Running csvstack on {len(temp_files)} files...")

        # Run csvstack
        with open(output_csv, "w") as f:
            subprocess.run(cmd, stdout=f, check=True)

        print(f"Combined CSV saved to {output_csv}")
        print(f"Output has {len(target_columns)} columns as specified")

    finally:
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
