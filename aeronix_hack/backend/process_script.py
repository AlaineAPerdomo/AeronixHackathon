# process_script.py
import sys
import time
import os, logging

def main():
    if len(sys.argv) < 3:
        print("Usage: python process_script.py <netlist_file> <csv_file>")
        sys.exit(1)

    netlist_path = sys.argv[1]
    csv_path = sys.argv[2]

    # Confirm the files exist
    if not os.path.exists(netlist_path) or not os.path.exists(csv_path):
        logging.error("One or both input files do not exist.")
        sys.exit(1)

    logging.info(f"Processing netlist: {netlist_path}")
    time.sleep(2)

    logging.info(f"Processing CSV: {csv_path}")
    time.sleep(2)

    logging.info("Combining data...")
    time.sleep(2)

    logging.info("Processing finished successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
