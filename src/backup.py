import os
import time
import requests
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env vars for local testing
load_dotenv()

MEALIE_URL = os.getenv("MEALIE_URL", "").rstrip("/")
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN", "")
BACKUP_PATH = Path(os.getenv("BACKUP_PATH", "/backups"))
SUCCESS_URL = os.getenv("SUCCESS_URL", "")
KEEP_BACKUPS = int(os.getenv("KEEP_BACKUPS", "5"))
FILENAME = os.getenv("BACKUP_FILENAME", "mealie-backup-latest.zip")


def get_backups_list(data):
    """Extracts the list of backups from the API response."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ["backups", "imports", "items"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        for val in data.values():
            if isinstance(val, list):
                return val
    return []


def main():
    print("--- Mealie Backup Process Starting ---")
    if not MEALIE_URL or not MEALIE_TOKEN:
        print("Error: MEALIE_URL and MEALIE_TOKEN must be set.")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {MEALIE_TOKEN}",
        "Content-Type": "application/json",
    }

    # 1. Trigger Backup
    print(f"Triggering backup on {MEALIE_URL}...")
    try:
        response = requests.post(f"{MEALIE_URL}/api/admin/backups", headers=headers)
        response.raise_for_status()
        print("Backup creation triggered successfully.")
    except Exception as e:
        print(f"Error triggering backup: {e}")
        sys.exit(1)

    # 2. Find the latest backup (Wait for completion and poll)
    print("Waiting for backup to complete...")
    time.sleep(10)

    latest_backup = None
    for i in range(12):
        try:
            backups_resp = requests.get(
                f"{MEALIE_URL}/api/admin/backups", headers=headers
            )
            backups_resp.raise_for_status()
            data = backups_resp.json()
            backups = get_backups_list(data)

            if backups and len(backups) > 0:
                latest_backup = backups[0]
                print(f"Found latest backup: {latest_backup['name']}")
                break
        except Exception as e:
            print(f"Error listing backups: {e}")

        print(f"Retrying list ({i+1}/12)...")
        time.sleep(5)

    if not latest_backup:
        print("Could not find any backups after creation.")
        sys.exit(1)

    # 3. Download Backup (Two-step process)
    source_filename = latest_backup["name"]

    # Step A: Get the File Token
    print(f"Requesting download token for {source_filename}...")
    try:
        token_resp = requests.get(
            f"{MEALIE_URL}/api/admin/backups/{source_filename}", headers=headers
        )
        token_resp.raise_for_status()
        file_token = token_resp.json().get("fileToken")

        if not file_token:
            print(f"Error: Could not find 'fileToken' in response: {token_resp.text}")
            sys.exit(1)

        # Step B: Download using the token
        download_url = f"{MEALIE_URL}/api/utils/download?token={file_token}"
        dest_file = BACKUP_PATH / FILENAME

        print(f"Downloading file via utility endpoint...")
        BACKUP_PATH.mkdir(parents=True, exist_ok=True)

        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(dest_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        os.sync()
        if dest_file.exists():
            size = dest_file.stat().st_size
            print(f"Download complete. File size: {size} bytes.")
            if size < 1000:
                print(
                    f"Error: Downloaded file is too small ({size} bytes). Handshake failed."
                )
                sys.exit(1)
        else:
            print(f"Error: File {dest_file} does not exist after download attempt.")
            sys.exit(1)

    except Exception as e:
        print(f"Error during download handshake: {e}")
        sys.exit(1)

    # 4. Cleanup Mealie Backups (Keep only X)
    print(f"Cleaning up Mealie backups (keeping last {KEEP_BACKUPS})...")
    try:
        backups_resp = requests.get(f"{MEALIE_URL}/api/admin/backups", headers=headers)
        backups_resp.raise_for_status()
        all_backups = get_backups_list(backups_resp.json())

        if len(all_backups) > KEEP_BACKUPS:
            to_delete = all_backups[KEEP_BACKUPS:]
            for backup in to_delete:
                name = backup["name"]
                print(f"Deleting old backup from Mealie: {name}")
                requests.delete(
                    f"{MEALIE_URL}/api/admin/backups/{name}", headers=headers
                )
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")

    # 5. Success Ping
    if SUCCESS_URL:
        print(f"Pinging success URL: {SUCCESS_URL}")
        try:
            requests.get(SUCCESS_URL, timeout=10)
        except:
            pass

    print("Mealie backup process finished successfully.")


if __name__ == "__main__":
    main()
