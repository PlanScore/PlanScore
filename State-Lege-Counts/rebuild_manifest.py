#!/usr/bin/env python3
"""
Rebuild manifest.json from existing result files and original zip files.
"""
import json
import sys
import os
import glob

def main():
    if len(sys.argv) < 3:
        print("Usage: rebuild_manifest.py <results_dir> <input_dir>")
        sys.exit(1)

    results_dir = sys.argv[1]
    input_dir = sys.argv[2]

    # Get all result .txt files
    result_files = glob.glob(os.path.join(results_dir, "*.txt"))

    # Get all input zip files
    zip_files = glob.glob(os.path.join(input_dir, "*.zip"))

    # Create postal code to FIPS code mapping
    postal_to_fips = {
        'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06', 'CO': '08',
        'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13', 'HI': '15', 'ID': '16',
        'IL': '17', 'IN': '18', 'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22',
        'ME': '23', 'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
        'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
        'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39', 'OK': '40',
        'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45', 'SD': '46', 'TN': '47',
        'TX': '48', 'UT': '49', 'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54',
        'WI': '55', 'WY': '56'
    }

    # Create mapping from postal code to actual zip filename
    postal_to_zip = {}
    for zip_file in zip_files:
        basename = os.path.basename(zip_file)

        # Try to determine state from filename
        matched_state = None

        # First try: tl_2025_XX_sldl.zip format
        if basename.startswith("tl_2025_"):
            parts = basename.split("_")
            if len(parts) >= 3:
                fips = parts[2]
                # Find postal code for this FIPS
                for postal, f in postal_to_fips.items():
                    if f == fips:
                        matched_state = postal
                        break

        # Second try: look for state postal code anywhere in filename
        if not matched_state:
            for postal in postal_to_fips.keys():
                if postal.lower() in basename.lower():
                    matched_state = postal
                    break

        if matched_state:
            postal_to_zip[matched_state] = basename

    results = []

    for result_file in sorted(result_files):
        basename = os.path.basename(result_file)
        # Format: STATE_PLANID.txt
        parts = basename.split("_")
        if len(parts) < 2:
            continue

        state_postal = parts[0]
        plan_id = "_".join(parts[1:]).replace(".txt", "")

        # Find matching zip file
        zip_filename = postal_to_zip.get(state_postal)
        if not zip_filename:
            print(f"WARNING: No zip file found for state {state_postal}")
            zip_filename = f"unknown_{state_postal}.zip"

        plan_url = f"https://dev.planscore.org/plan.html?{plan_id}"

        results.append({
            "state": state_postal,
            "file": result_file,
            "filename": zip_filename,
            "plan_url": plan_url,
            "success": True
        })

    print(f"Rebuilt manifest with {len(results)} entries")

    # Save manifest
    manifest_file = os.path.join(results_dir, "manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Manifest saved to {manifest_file}")


if __name__ == "__main__":
    main()
