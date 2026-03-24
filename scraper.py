import argparse
import sys
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://result.mdu.ac.in/postexam/result.aspx"
DEFAULT_OUTPUT = "result.html"

def _collect_form_data(soup: BeautifulSoup) -> Dict[str, str]:
    form = soup.find("form")
    container = form if form is not None else soup
    payload: Dict[str, str] = {}

    for field in container.find_all("input"):
        name = field.get("name") or field.get("id")
        if not name:
            continue
        payload[name] = field.get("value", "")

    return payload

def _find_text_fields(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    form = soup.find("form")
    container = form if form is not None else soup

    text_inputs = [
        field
        for field in container.find_all("input")
        if field.get("type", "text").lower() in {"text", ""}
    ]

    reg_field = None
    roll_field = None

    for field in text_inputs:
        key = field.get("name") or field.get("id") or ""
        if "reg" in key.lower():
            reg_field = key
            break

    for field in text_inputs:
        key = field.get("name") or field.get("id") or ""
        if "roll" in key.lower():
            roll_field = key
            break

    if not reg_field and text_inputs:
        reg_field = text_inputs[0].get("name") or text_inputs[0].get("id")

    if not roll_field and len(text_inputs) > 1:
        roll_field = text_inputs[1].get("name") or text_inputs[1].get("id")

    return {"reg": reg_field, "roll": roll_field}

def _find_submit_field(soup: BeautifulSoup) -> Optional[Dict[str, str]]:
    form = soup.find("form")
    container = form if form is not None else soup

    for field in container.find_all("input"):
        field_type = field.get("type", "").lower()
        if field_type in {"submit", "button"}:
            name = field.get("name") or field.get("id")
            if name:
                return {name: field.get("value", "Submit")}

    button = container.find("button")
    if button:
        name = button.get("name") or button.get("id")
        if name:
            return {name: button.get("value", "Submit")}

    return None

def fetch_result(registration_no: str, roll_no: str, output_path: str = DEFAULT_OUTPUT) -> str:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "ResultFinderScraper/1.0 (+https://result.mdu.ac.in/postexam/result.aspx)"
        }
    )

    response = session.get(BASE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    payload = _collect_form_data(soup)
    fields = _find_text_fields(soup)

    if not fields.get("reg") or not fields.get("roll"):
        raise RuntimeError(
            "Unable to locate registration/roll number fields on the page. "
            "Please verify the form structure."
        )

    payload[fields["reg"]] = registration_no
    payload[fields["roll"]] = roll_no

    submit = _find_submit_field(soup)
    if submit:
        payload.update(submit)

    result_response = session.post(BASE_URL, data=payload, timeout=30)
    result_response.raise_for_status()

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(result_response.text)

    return output_path

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch MDU result HTML by registration number and roll number."
    )
    parser.add_argument("registration_no", help="Registration number")
    parser.add_argument("roll_no", help="Roll number")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output HTML file path (default: {DEFAULT_OUTPUT})",
    )

    args = parser.parse_args()

    try:
        output_file = fetch_result(args.registration_no, args.roll_no, args.output)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Saved result HTML to {output_file}")

if __name__ == "__main__":
    main()