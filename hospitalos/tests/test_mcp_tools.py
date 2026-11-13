"""
tests/test_mcp_tools.py — Tests for every tool of the 6 custom hospital MCP servers.

The tool functions are plain Python functions (FastMCP's @mcp.tool() returns them
unchanged), so we can call them directly. That is fast and tests the real logic.
Each test gets a fresh copy of the seeded database (see conftest.py).

Run:  python -m pytest -v
"""

import json
from datetime import datetime, timedelta

from mcp_servers.appointments import server as appointments
from mcp_servers.beds import server as beds
from mcp_servers.billing import server as billing
from mcp_servers.lab import server as lab
from mcp_servers.patients import server as patients
from mcp_servers.pharmacy import server as pharmacy


def as_json(text: str) -> dict:
    """Parse a successful tool result (fails the test with the text if it was an error)."""
    assert not text.startswith("Friendly"), text
    return json.loads(text)


def future(days=7, hour=11) -> str:
    return (datetime.now() + timedelta(days=days)).strftime(f"%Y-%m-%dT{hour:02d}:00")


# ---------------- beds ----------------
def test_get_free_beds_icu():
    data = as_json(beds.get_free_beds("icu"))           # case-insensitive
    assert data["ward"] == "ICU"
    assert data["free_count"] == len(data["free_beds"]) == 8


def test_get_free_beds_unknown_ward_is_friendly():
    text = beds.get_free_beds("Mars")
    assert text.startswith("Friendly Error") and "ICU" in text


def test_admit_then_discharge():
    admitted = as_json(beds.admit_patient(3, "ICU"))
    assert admitted["status"] == "success" and admitted["patient_id"] == 3
    assert as_json(beds.get_free_beds("ICU"))["free_count"] == 7
    discharged = as_json(beds.discharge_patient(3))
    assert discharged["bed_number"] == admitted["bed_number"]


def test_admit_already_admitted_patient_refused():
    assert "already admitted" in beds.admit_patient(1, "ICU")


def test_beds_input_validation():
    assert beds.admit_patient(-1, "ICU").startswith("Friendly Error")
    assert beds.discharge_patient(3).startswith("Friendly")   # patient 3 is not in a bed


# ---------------- patients ----------------
def test_search_patients():
    data = as_json(patients.search_patients("meera"))
    assert data["count"] >= 1 and data["patients"][0]["full_name"] == "Meera Nair"


def test_search_patients_no_match():
    assert "No patients found" in patients.search_patients("zzzz")


def test_get_patient_and_missing():
    assert as_json(patients.get_patient(1))["patient"]["full_name"] == "Aarav Sharma"
    assert patients.get_patient(9999).startswith("Friendly Error")


def test_patient_history_has_related_records():
    data = as_json(patients.get_patient_history(1))
    assert data["patient"]["id"] == 1
    assert "bills" in data


# ---------------- appointments ----------------
def test_doctor_availability():
    data = as_json(appointments.list_doctor_availability(1, future()[:10]))
    assert data["doctor_name"] == "Dr. Rajesh Menon"
    assert "open_slots" in data


def test_doctor_availability_bad_date():
    assert appointments.list_doctor_availability(1, "not-a-date").startswith("Friendly Error")


def test_book_and_cancel_appointment():
    booked = as_json(appointments.book_appointment(3, 1, future()))
    appt_id = booked["appointment"]["id"]
    assert any(a["id"] == appt_id for a in as_json(appointments.list_appointments(3))["appointments"])
    assert as_json(appointments.cancel_appointment(appt_id))["appointment"]["status"] == "Cancelled"


def test_no_double_booking():
    when = future(days=8, hour=10)
    as_json(appointments.book_appointment(3, 1, when))
    second = appointments.book_appointment(5, 1, when)      # same doctor, same time
    assert second.startswith("Friendly Error") and "already has an appointment" in second


def test_cannot_book_in_the_past():
    assert "in the past" in appointments.book_appointment(3, 1, "2020-01-01T10:00")


def test_cannot_book_unavailable_doctor():
    assert "unavailable" in appointments.book_appointment(3, 5, future())   # doctor 5 is off duty


def test_cancel_missing_appointment():
    assert appointments.cancel_appointment(99999).startswith("Friendly Error")


# ---------------- pharmacy ----------------
def test_check_stock_partial_name():
    data = as_json(pharmacy.check_stock("paracetamol"))
    assert data["medicines"][0]["name"] == "Paracetamol 650mg"


def test_check_stock_unknown():
    assert "No medicine matching" in pharmacy.check_stock("Unobtainium")


def test_low_stock_sorted_and_below_threshold():
    data = as_json(pharmacy.list_low_stock(50))
    quantities = [m["stock_quantity"] for m in data["medicines"]]
    assert quantities and all(q < 50 for q in quantities)
    assert quantities == sorted(quantities)


def test_restock_and_validation():
    data = as_json(pharmacy.restock_medicine("Paracetamol 650mg", 10))
    assert data["medicine"]["new_stock_quantity"] == data["medicine"]["previous_stock"] + 10
    assert pharmacy.restock_medicine("Paracetamol 650mg", -5).startswith("Friendly Error")


# ---------------- lab ----------------
def test_pending_tests_are_pending():
    data = as_json(lab.list_pending_tests())
    assert data["pending_count"] == len(data["pending_tests"]) > 0


def test_get_results():
    data = as_json(lab.get_results(1))
    assert data["patient_name"] == "Aarav Sharma" and data["count"] >= 1


def test_order_test_and_validation():
    data = as_json(lab.order_test(2, "ECG"))
    assert data["lab_test"]["status"] == "Pending"
    assert lab.order_test(9999, "ECG").startswith("Friendly Error")
    assert lab.order_test(2, "").startswith("Friendly Error")


# ---------------- billing ----------------
def test_get_bill():
    data = as_json(billing.get_bill(1))
    assert data["patient_name"] == "Aarav Sharma" and data["invoice_count"] >= 1


def test_unpaid_bills_exclude_paid():
    data = as_json(billing.list_unpaid_bills())
    assert data["unpaid_count"] > 0
    assert all(b["paid_status"] != "Paid" for b in data["unpaid_bills"])


def test_mark_bill_paid_once():
    assert as_json(billing.mark_bill_paid(2))["bill"]["paid_status"] == "Paid"
    assert "already marked as Paid" in billing.mark_bill_paid(2)
    assert billing.mark_bill_paid(99999).startswith("Friendly Error")
