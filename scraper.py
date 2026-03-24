import requests
from bs4 import BeautifulSoup
import time
import csv

URL = "https://result.mdu.ac.in/postexam/result.aspx"

known_students = [
    ("2413761085", "7086802"),
    ("2413761004", "7086803"),
    ("2413761005", "7086804"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": URL
}

results = []   # store all valid students


def get_hidden_fields(session):
    try:
        res = session.get(URL, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        viewstate = soup.find("input", {"name": "__VIEWSTATE"})
        eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})

        if not viewstate or not eventvalidation:
            return None, None

        return viewstate["value"], eventvalidation["value"]

    except:
        return None, None


def fetch_result(session, reg, roll):
    viewstate, eventvalidation = get_hidden_fields(session)

    if not viewstate:
        return False

    payload = {
        "__VIEWSTATE": viewstate,
        "__EVENTVALIDATION": eventvalidation,
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "txtRegNo": reg,
        "txtRollNo": roll,
        "btnSearch": "Search"
    }

    try:
        response = session.post(URL, data=payload, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        text = soup.get_text()

        # ✅ check valid result
        if "Name" in text and "Result" in text:

            name = ""
            result_status = ""

            # extract info
            for line in text.split("\n"):
                if "Name" in line and name == "":
                    name = line.strip()
                if "Result" in line:
                    result_status = line.strip()

            print(f"✅ FOUND: {reg} | {roll} | {name}")

            results.append([reg, roll, name, result_status])
            return True

    except Exception as e:
        print(f"⚠️ Error: {e}")

    return False


def save_to_excel():
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Reg No", "Roll No", "Name", "Result"])

        for row in results:
            writer.writerow(row)

    print("\n📄 Results saved to results.csv")


def smart_scan():
    session = requests.Session()
    found = set()

    print("🚀 Starting Smart Scan...\n")

    for reg, roll in known_students:
        base_reg = int(reg)
        base_roll = int(roll)

        # ✅ SAFE RANGE (important fix)
        for r in range(base_reg - 5, base_reg + 6):
            for rl in range(base_roll - 2, base_roll + 3):

                key = (r, rl)
                if key in found:
                    continue

                print(f"🔍 Trying: {r} | {rl}")

                success = fetch_result(session, str(r), str(rl))

                if success:
                    found.add(key)

                time.sleep(2)   # ✅ safe delay

    print("\n✅ Scan Complete")
    print(f"Total Found: {len(results)}")

    save_to_excel()


# ▶️ Run
smart_scan()
