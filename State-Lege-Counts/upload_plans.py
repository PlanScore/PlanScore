#!/usr/bin/env python3
"""
Upload state legislative district plans to PlanScore API and retrieve results.
"""
import json
import time
import sys
import os
import requests
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import preprocess function from same directory
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)
from preprocess_plan import preprocess_plan

API_BASE = "https://api.dev.planscore.org"
AUTH_TOKEN = "Good"
POLL_INTERVAL = 10  # seconds
MAX_RETRIES = 60  # 10 minutes max
PARALLEL_UPLOADS = 10  # Number of parallel uploads


def upload_plan(zip_path):
    """Upload a zip file to the PlanScore API using multistep process."""
    print(f"Uploading {zip_path}...")

    # Get S3 upload fields
    headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    response = requests.get(f"{API_BASE}/upload", headers=headers)
    response.raise_for_status()

    s3_url, form_fields = response.json()

    # Upload file to S3
    filename = os.path.basename(zip_path)
    with open(zip_path, "rb") as f:
        files = {"file": (filename, f)}
        data = form_fields.copy()

        # Don't follow redirects automatically so we can capture the redirect URL
        response = requests.post(s3_url, data=data, files=files, allow_redirects=False)
        response.raise_for_status()

    # S3 returns a 303 redirect to the success_action_redirect URL
    if response.status_code in (303, 302, 301):
        redirect_url = response.headers.get("Location")
        print(f"  S3 upload complete, redirect URL: {redirect_url}")

        # The redirect URL contains query parameters we need
        # According to the API spec, we POST to /uploaded endpoint
        # Let's POST with empty body and the auth header
        for attempt in range(3):
            try:
                time.sleep(2)  # Brief delay
                response = requests.post(redirect_url, headers=headers, json={}, timeout=30)
                response.raise_for_status()

                result = response.json()
                print(f"  Got index_url: {result['index_url']}")
                return result["index_url"]
            except requests.exceptions.HTTPError as e:
                if attempt < 2:
                    print(f"  Retry {attempt+1}/3 after error: {e}")
                    time.sleep(5)
                else:
                    raise

        raise Exception("Failed to get index_url after retries")
    else:
        raise Exception(f"Unexpected S3 response: {response.status_code}")


def wait_for_completion(index_url):
    """Poll index.json until scoring is complete."""
    print(f"Waiting for scoring to complete: {index_url}")

    for i in range(MAX_RETRIES):
        try:
            response = requests.get(index_url)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == True:
                print(f"Scoring complete!")
                return data

            print(f"  Status: {data.get('message', 'In progress')}... (attempt {i+1}/{MAX_RETRIES})")
            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"  Error checking status: {e}")
            time.sleep(POLL_INTERVAL)

    raise Exception(f"Timeout waiting for {index_url}")


def get_index_txt(index_url):
    """Retrieve index.txt from the same location as index.json."""
    txt_url = index_url.replace("index.json", "index.txt")
    print(f"Retrieving {txt_url}...")

    response = requests.get(txt_url)
    response.raise_for_status()

    return response.text


def process_plan(zip_path, output_dir, ordered_dir):
    """Upload a plan, wait for completion, and retrieve index.txt."""
    try:
        # Preprocess the plan (filter ZZZ, sort numerically)
        print(f"Preprocessing {zip_path}...")
        ordered_zip = preprocess_plan(zip_path, ordered_dir)

        # Upload the ordered version
        index_url = upload_plan(ordered_zip)

        # Wait for completion
        index_data = wait_for_completion(index_url)

        # Get state postal code and plan ID from index data
        state = index_data.get("model", {}).get("state", "XX")
        plan_id = index_data.get("id", "unknown")
        filename = os.path.basename(zip_path)

        # Build plan URL
        plan_url = f"https://dev.planscore.org/plan.html?{plan_id}"

        # Retrieve index.txt
        txt_content = get_index_txt(index_url)

        # Save to output directory
        output_file = os.path.join(output_dir, f"{state}_{plan_id}.txt")
        with open(output_file, "w") as f:
            f.write(txt_content)

        print(f"Saved to {output_file}")
        return {
            "state": state,
            "file": output_file,
            "filename": filename,
            "plan_url": plan_url,
            "success": True
        }

    except Exception as e:
        print(f"ERROR processing {zip_path}: {e}")
        return {
            "state": "XX",
            "file": None,
            "filename": os.path.basename(zip_path),
            "plan_url": None,
            "success": False
        }


def main():
    if len(sys.argv) < 4:
        print("Usage: upload_plans.py <output_dir> <ordered_dir> <zip_file1> [zip_file2] ...")
        sys.exit(1)

    output_dir = sys.argv[1]
    ordered_dir = sys.argv[2]
    zip_files = sys.argv[3:]

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(ordered_dir, exist_ok=True)

    print(f"Processing {len(zip_files)} plans with {PARALLEL_UPLOADS} parallel workers...")
    print(f"Ordered files will be saved to: {ordered_dir}")

    results = []

    # Process plans in parallel
    with ThreadPoolExecutor(max_workers=PARALLEL_UPLOADS) as executor:
        # Submit all tasks
        future_to_zip = {
            executor.submit(process_plan, zip_path, output_dir, ordered_dir): zip_path
            for zip_path in zip_files
        }

        # Collect results as they complete
        for future in as_completed(future_to_zip):
            zip_path = future_to_zip[future]
            try:
                result = future.result()
                results.append(result)
                print()
            except Exception as e:
                print(f"ERROR with {zip_path}: {e}")
                results.append({
                    "state": "XX",
                    "file": None,
                    "filename": os.path.basename(zip_path),
                    "plan_url": None,
                    "success": False
                })

    # Summary
    successful = [r for r in results if r["success"]]
    print(f"\nProcessed {len(successful)}/{len(results)} plans successfully")

    # Save results manifest
    manifest_file = os.path.join(output_dir, "manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Manifest saved to {manifest_file}")


if __name__ == "__main__":
    main()
