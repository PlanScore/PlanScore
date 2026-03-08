#!/usr/bin/env python3
"""
Preprocess state legislative district plan files:
1. Filter out rows where district field = "ZZZ"
2. Sort numerically by district field (DISTRICT, SLDLST, or SLDUST)
3. Create new zip file with "-ordered" suffix
"""
import os
import sys
import tempfile
import shutil
import subprocess
import zipfile
import glob


def find_shapefile(directory):
    """Find the .shp file in a directory."""
    shp_files = glob.glob(os.path.join(directory, "*.shp"))
    if not shp_files:
        raise Exception(f"No shapefile found in {directory}")
    return shp_files[0]


def get_district_field(shapefile_path):
    """Determine which district field exists in the shapefile."""
    result = subprocess.run(
        ["ogrinfo", "-al", "-so", shapefile_path],
        capture_output=True,
        text=True,
        check=True
    )

    output = result.stdout

    # Check for each possible district field
    if "DISTRICT:" in output:
        return "DISTRICT"
    elif "SLDLST:" in output:
        return "SLDLST"
    elif "SLDUST:" in output:
        return "SLDUST"
    else:
        raise Exception(f"No district field found in {shapefile_path}")


def preprocess_shapefile(input_shp, output_shp, district_field):
    """
    Filter and sort shapefile using ogr2ogr.
    Filters out rows where district_field = 'ZZZ'
    Sorts numerically by district_field (casting to integer for numeric sort)
    """
    # Get layer name from input shapefile
    layer_name = os.path.splitext(os.path.basename(input_shp))[0]

    # Build SQL query
    # CAST to integer for numeric sorting, but need to handle non-numeric values
    # We'll filter ZZZ first, then try to sort numerically
    # Use <> instead of != and -dialect SQLite for better SQL support
    sql = f"""
    SELECT * FROM "{layer_name}"
    WHERE {district_field} <> 'ZZZ'
    ORDER BY CAST({district_field} AS INTEGER)
    """

    # Run ogr2ogr with SQLite dialect
    cmd = [
        "ogr2ogr",
        "-f", "ESRI Shapefile",
        "-dialect", "SQLite",
        output_shp,
        input_shp,
        "-sql", sql
    ]

    subprocess.run(cmd, check=True, capture_output=True)


def create_zip_from_directory(source_dir, output_zip):
    """Create a zip file from all files in a directory."""
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)


def preprocess_plan(input_zip, output_dir=None):
    """
    Preprocess a plan zip file.
    Returns path to the new preprocessed zip file.
    """
    print(f"Preprocessing {input_zip}...")

    # Create temp directories
    extract_dir = tempfile.mkdtemp(prefix="extract_")
    process_dir = tempfile.mkdtemp(prefix="process_")

    try:
        # Extract input zip
        with zipfile.ZipFile(input_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Find shapefile
        input_shp = find_shapefile(extract_dir)
        base_name = os.path.splitext(os.path.basename(input_shp))[0]

        # Determine district field
        district_field = get_district_field(input_shp)
        print(f"  Found district field: {district_field}")

        # Create output shapefile path
        output_shp = os.path.join(process_dir, f"{base_name}.shp")

        # Preprocess
        preprocess_shapefile(input_shp, output_shp, district_field)
        print(f"  Filtered and sorted by {district_field}")

        # Create output zip with "-ordered" suffix
        input_filename = os.path.basename(input_zip)
        input_base = os.path.splitext(input_filename)[0]
        output_filename = f"{input_base}-ordered.zip"

        # Place in specified output directory or same as input
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_zip = os.path.join(output_dir, output_filename)
        else:
            input_dir = os.path.dirname(input_zip)
            output_zip = os.path.join(input_dir, output_filename)

        create_zip_from_directory(process_dir, output_zip)
        print(f"  Created {output_zip}")

        return output_zip

    finally:
        # Cleanup
        shutil.rmtree(extract_dir, ignore_errors=True)
        shutil.rmtree(process_dir, ignore_errors=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: preprocess_plan.py <input.zip> [output_dir]")
        sys.exit(1)

    input_zip = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    output_zip = preprocess_plan(input_zip, output_dir)
    print(f"Output: {output_zip}")


if __name__ == "__main__":
    main()
