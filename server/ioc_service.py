import os
import sys
import time
import csv
import json
from datetime import datetime
from ioc_fetch.ioc_call import get_ip_info

def main():
    if len(sys.argv) != 2:
        print("Usage: python ioc_service.py <path_to_ip_list.txt>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"[!] Input file not found: {input_file}")
        sys.exit(1)

    # Read IPs from file
    with open(input_file, "r") as f:
        ips = [line.strip() for line in f if line.strip()]

    if not ips:
        print("[!] No valid IPs found in input file.")
        sys.exit(1)

    print(f"[*] Starting IOC lookup for {len(ips)} IPs...\n")

    # Prepare output file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_output = f"ioc_results_{timestamp}.csv"
    json_output = f"ioc_results_{timestamp}.json"
    start_time = time.time()

    results = []

    try:
        with open(csv_output, "w", newline="", buffering=1) as csvfile:
            writer = csv.writer(csvfile)
            # Write CSV header
            writer.writerow(["IP", "Classification", "Flagged", "ASN", "Organization", "Country"])

            for idx, ip in enumerate(ips, start=1):
                print(f"[{idx}/{len(ips)}] Processing {ip}...")
                try:
                    result = get_ip_info(ip)  
                except Exception as e:
                    print(f"    [!] Error fetching {ip}: {e}")
                    result = {
                        "ip": ip,
                        "classification": "ERROR",
                        "flagged": None,
                        "asn": None,
                        "org": None,
                        "country": None
                    }

                # Print to console
                print(f"    → {json.dumps(result, indent=2)}")

                # Write to CSV
                writer.writerow([
                    result.get("ip", ""),
                    result.get("classification", ""),
                    result.get("flagged", ""),
                    result.get("asn", ""),
                    result.get("org", ""),
                    result.get("country", "")
                ])

                results.append(result)

        with open(json_output, "w", encoding="utf-8") as jf:
            json.dump(results, jf, indent=2, ensure_ascii=False)

        elapsed = time.time() - start_time
        print(f"\n[*] Completed IOC classification in {elapsed:.2f}s")
        print(f"[*] CSV saved to: {csv_output}")
        print(f"[*] JSON saved to: {json_output}")

    except IOError as e:
        print(f"[!] File write error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
