#!/usr/bin/env python3
"""
Mara Smart Herd Tracker
========================
A runnable prototype of the Sprint 1 MVP described in the project plan:

  Story 1: Register cattle with a unique RFID number
  Story 2: View herd dashboard (all registered cattle + status)
  Story 3: Simulate RFID reader entry/exit detection at the mobile boma
  Story 4: Report a missing animal

This is a self-contained command-line simulation of the real system.
In production, Story 3's "scan" would come from a physical UHF RFID
reader instead of manual/random input, and Story 4's alert would be
pushed via Firebase Cloud Messaging to conservancy rangers.

Run it with:
    python3 mara_smart_herd_tracker.py

Data is stored in herd_data.json in the same folder, so your herd
persists between runs.
"""

import json
import os
import random
import string
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "herd_data.json")


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"cattle": {}, "events": [], "lost_reports": []}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_rfid():
    """Simulate a unique 12-digit ISO 11784/11785 style RFID tag number."""
    return "".join(random.choices(string.digits, k=12))


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Story 1: Register a cow with a unique RFID microchip
# ---------------------------------------------------------------------------

def register_cattle(data):
    print("\n--- Register New Animal (Story 1) ---")
    name = input("Animal name / tag label: ").strip()
    if not name:
        print("Name cannot be empty.")
        return
    owner = input("Owner name: ").strip() or "Unknown"
    breed = input("Breed (e.g., Boran, Zebu) [optional]: ").strip() or "N/A"

    rfid = generate_rfid()
    while rfid in data["cattle"]:
        rfid = generate_rfid()

    data["cattle"][rfid] = {
        "name": name,
        "owner": owner,
        "breed": breed,
        "status": "In Boma",
        "registered_on": now(),
        "last_event": None,
    }
    save_data(data)
    print(f"\nRegistered '{name}' successfully.")
    print(f"Assigned unique RFID number: {rfid}")
    print("Keep this number safe — it is this animal's permanent digital identity.")


# ---------------------------------------------------------------------------
# Story 2: View herd dashboard
# ---------------------------------------------------------------------------

def view_dashboard(data):
    print("\n--- Herd Dashboard (Story 2) ---")
    if not data["cattle"]:
        print("No cattle registered yet. Use option 1 to register an animal.")
        return

    header = f"{'RFID':14} {'Name':15} {'Owner':15} {'Breed':10} {'Status':12} {'Registered On'}"
    print(header)
    print("-" * len(header))
    for rfid, c in data["cattle"].items():
        print(f"{rfid:14} {c['name']:15} {c['owner']:15} {c['breed']:10} {c['status']:12} {c['registered_on']}")

    total = len(data["cattle"])
    missing = sum(1 for c in data["cattle"].values() if c["status"] == "Missing")
    print(f"\nTotal herd size: {total}   |   Missing: {missing}   |   In Boma/Grazing: {total - missing}")


# ---------------------------------------------------------------------------
# Story 3: RFID reader entry/exit detection at the mobile boma
# ---------------------------------------------------------------------------

def scan_rfid(data):
    print("\n--- RFID Reader Simulation: Boma Entry/Exit (Story 3) ---")
    if not data["cattle"]:
        print("No cattle registered yet.")
        return

    rfid = input("Scan (enter) RFID number of the animal passing the reader: ").strip()
    animal = data["cattle"].get(rfid)
    if not animal:
        print("Unrecognized tag — this RFID is not registered in the system.")
        return

    # Toggle status like a real gate reader would (entering vs leaving)
    if animal["status"] == "In Boma":
        animal["status"] = "Grazing (Out of Boma)"
        direction = "EXIT"
    else:
        animal["status"] = "In Boma"
        direction = "ENTRY"

    event = {
        "timestamp": now(),
        "rfid": rfid,
        "animal": animal["name"],
        "direction": direction,
    }
    data["events"].append(event)
    animal["last_event"] = event
    save_data(data)

    print(f"[{event['timestamp']}] {direction} recorded for '{animal['name']}' (RFID {rfid}).")
    print(f"Current status: {animal['status']}")


def view_event_log(data):
    print("\n--- Boma Entry/Exit Log ---")
    if not data["events"]:
        print("No RFID scan events yet.")
        return
    for e in data["events"][-20:]:
        print(f"[{e['timestamp']}] {e['direction']:5} - {e['animal']} (RFID {e['rfid']})")


# ---------------------------------------------------------------------------
# Story 4: Report a missing animal
# ---------------------------------------------------------------------------

def report_lost(data):
    print("\n--- Report Missing Animal (Story 4) ---")
    if not data["cattle"]:
        print("No cattle registered yet.")
        return

    rfid = input("RFID number of the missing animal: ").strip()
    animal = data["cattle"].get(rfid)
    if not animal:
        print("Unrecognized tag — this RFID is not registered in the system.")
        return

    location = input("Last known location (e.g., 'Northern grazing block'): ").strip() or "Unknown"
    reporter = input("Reported by: ").strip() or "Unknown"

    animal["status"] = "Missing"
    report = {
        "timestamp": now(),
        "rfid": rfid,
        "animal": animal["name"],
        "owner": animal["owner"],
        "last_known_location": location,
        "reported_by": reporter,
    }
    data["lost_reports"].append(report)
    save_data(data)

    print(f"\nLost-animal report filed for '{animal['name']}' (RFID {rfid}).")
    print("Alert simulated: nearby conservancy rangers have been notified.")


def view_lost_reports(data):
    print("\n--- Active Lost / Missing Reports ---")
    active = [r for r in data["lost_reports"] if data["cattle"].get(r["rfid"], {}).get("status") == "Missing"]
    if not active:
        print("No animals currently reported missing.")
        return
    for r in active:
        print(f"[{r['timestamp']}] {r['animal']} (RFID {r['rfid']}) - Owner: {r['owner']} "
              f"- Last seen: {r['last_known_location']} - Reported by: {r['reported_by']}")


def mark_recovered(data):
    print("\n--- Mark Animal Recovered ---")
    rfid = input("RFID number of the recovered animal: ").strip()
    animal = data["cattle"].get(rfid)
    if not animal:
        print("Unrecognized tag.")
        return
    if animal["status"] != "Missing":
        print(f"'{animal['name']}' is not currently marked missing.")
        return
    animal["status"] = "In Boma"
    save_data(data)
    print(f"'{animal['name']}' (RFID {rfid}) marked as recovered and back In Boma.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

MENU = """
====================================================
 MARA SMART HERD TRACKER  —  Sprint 1 MVP Prototype
 Mara North Conservancy
====================================================
 1. Register new animal (RFID)         [Story 1]
 2. View herd dashboard                [Story 2]
 3. Scan RFID at boma gate             [Story 3]
 4. View entry/exit log                [Story 3]
 5. Report missing animal              [Story 4]
 6. View active lost reports           [Story 4]
 7. Mark a missing animal as recovered
 0. Exit
----------------------------------------------------
"""


def main():
    data = load_data()
    print(MENU)
    while True:
        choice = input("Select an option: ").strip()
        if choice == "1":
            register_cattle(data)
        elif choice == "2":
            view_dashboard(data)
        elif choice == "3":
            scan_rfid(data)
        elif choice == "4":
            view_event_log(data)
        elif choice == "5":
            report_lost(data)
        elif choice == "6":
            view_lost_reports(data)
        elif choice == "7":
            mark_recovered(data)
        elif choice == "0":
            print("Kwaheri! Data saved to herd_data.json.")
            break
        else:
            print("Invalid option, please try again.")
        print(MENU)


if __name__ == "__main__":
    main()
