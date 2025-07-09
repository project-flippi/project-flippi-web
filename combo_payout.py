import time
import requests
import json
import re

# Store already processed lines
processed = set()

COMBO_FILE = "C:/Users/15613/project-flippi-web/combodata.txt"
BASE_URL = "http://127.0.0.1:8000"
processed_timestamps = set()

def parse_combos(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
    combo_blocks = [block.strip() for block in data.split('Timestamp:') if block.strip()]
    combolist = []

    for block in combo_blocks:
        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2})', block)
        timestamp = timestamp_match.group(1) if timestamp_match else None

        stage_match = re.search(r'StageID: (\d+)', block)
        stage_id = int(stage_match.group(1)) if stage_match else None

        players_match = re.search(r'Players: (\[.*?\])', block, re.DOTALL)
        players = json.loads(players_match.group(1)) if players_match else []

        moves_match = re.search(r'Moves: (\[.*?\])', block, re.DOTALL)
        moves = json.loads(moves_match.group(1)) if moves_match else []

        catcher_match = re.search(r'CatcherIndex: (\d+)', block)
        catcher_index = int(catcher_match.group(1)) if catcher_match else None

        start_percent_match = re.search(r'StartPercent: ([\d.]+)', block)
        start_percent = float(start_percent_match.group(1)) if start_percent_match else None

        end_percent_match = re.search(r'EndPercent: ([\d.]+)', block)
        end_percent = float(end_percent_match.group(1)) if end_percent_match else None

        did_kill_match = re.search(r'DidKill: (true|false)', block, re.IGNORECASE)
        did_kill = did_kill_match.group(1).lower() == 'true' if did_kill_match else False

        combo = {
            'Timestamp': timestamp,
            'StageID': stage_id,
            'Players': players,
            'CatcherIndex': catcher_index,
            'StartPercent': start_percent,
            'EndPercent': end_percent,
            'Moves': moves,
            'DidKill': did_kill
        }

        combolist.append(combo)
    return combolist

def get_wallet(tag):
    try:
        r = requests.get(f"{BASE_URL}/wallets/{tag.lower()}")
        if r.status_code == 200:
            return r.json()["wallet"]
    except Exception as e:
        print(f"[!] Error fetching wallet for {tag}: {e}")
    return None

def process_combos():
    try:
        combos = parse_combos(COMBO_FILE)
        if not combos:
            print("[…] No combos found in file.")
            return
    except Exception as e:
        print(f"[!] Error reading combo file: {e}")
        return

    for combo in combos:
        ts = combo.get("Timestamp")
        if not ts or ts in processed_timestamps:
            continue

        processed_timestamps.add(ts)
        players = combo.get("Players", [])
        catcher_index = combo.get("CatcherIndex")

        comboed = next((p for p in players if p["playerIndex"] == catcher_index), None)
        comboer = next((p for p in players if p["playerIndex"] != catcher_index), None)

        if not comboed or not comboer:
            print(f"[!] Invalid combo structure at {ts}")
            continue

        tag_attacker = comboer.get("nametag", "").strip()
        tag_defender = comboed.get("nametag", "").strip()

        if not tag_attacker or not tag_defender:
            print(f"[!] Missing nametag in combo at {ts}")
            continue

        wallet_attacker = get_wallet(tag_attacker)

        if wallet_attacker:
            print(f"{ts}: {tag_attacker} → {wallet_attacker}")
            print(f"Would send USDC: $2 to {wallet_attacker}")
        else:
            print(f"[!] Wallet not found for: {tag_attacker}")

if __name__ == "__main__":
    print(f"Watching {COMBO_FILE} for new combo entries...\n")
    while True:
        process_combos()
        time.sleep(2)