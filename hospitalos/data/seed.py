"""
seed.py — Synthetic Database Seeder for HospitalOS.

Fills all 8 tables with 100% fake (synthetic) data:
  - 5 wards (ICU, General, Pediatrics, Emergency, Maternity)
  - 60 beds, roughly half occupied
  - 100 patients, 15 doctors, ~50 medicines
  - ~60 appointments, ~50 lab tests, ~70 bills

The first few rows of every table are hand-written "core" records (stable IDs,
used by the MCP tests and the demo script). The rest are made with Faker.
A fixed random seed makes the data identical every time you run it.

Run from inside the hospitalos/ folder:
  python -m data.seed            # asks before wiping an existing database
  python -m data.seed --force    # wipes without asking
"""

import random
import sys
from datetime import datetime, timedelta, timezone

from faker import Faker

from backend import models
from backend.database import Base, SessionLocal, engine

SEED = 42
random.seed(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)

BLOOD_GROUPS = ["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"]
DIAGNOSES = [
    "Type 2 Diabetes Follow-up", "Hypertension", "Acute Bronchitis", "Dengue Fever",
    "Appendicitis", "Urinary Tract Infection", "Migraine", "Anemia", "Asthma",
    "Fractured Tibia", "Typhoid Fever", "Gastritis", "Pneumonia", "Chronic Kidney Disease",
    "Viral Fever", "Back Pain", "Skin Allergy", "Thyroid Disorder",
]
SPECIALIZATIONS = [
    "Cardiology", "Neurology", "Orthopedics", "Pediatrics", "Dermatology", "Oncology",
    "Gynecology", "ENT", "Ophthalmology", "Psychiatry", "Urology", "Radiology",
]
LAB_TESTS = [
    "Complete Blood Count", "Lipid Profile", "Liver Function Test", "Kidney Function Test",
    "Blood Glucose Fasting", "HbA1c", "Thyroid Panel", "Urine Routine", "Chest X-Ray",
    "ECG", "Dengue NS1 Antigen", "Vitamin D Level", "Arterial Blood Gas Panel",
]
LAB_RESULTS = [
    "Within normal limits", "Mildly elevated, recommend follow-up",
    "Slightly below range, supplement advised", "Abnormal, doctor review needed",
]
BILL_ITEMS = [
    "Consultation fee", "General Ward bed (2 days)", "Lab investigations",
    "Pharmacy medicines", "ICU bed (1 day)", "Minor procedure", "Physiotherapy session",
]
# (name, category, stock, unit_price, expiry) — a few have low stock on purpose
EXTRA_MEDICINES = [
    ("Ibuprofen 400mg", "Analgesic", 330), ("Azithromycin 500mg", "Antibiotic", 120),
    ("Pantoprazole 40mg", "Antacid", 260), ("Cetirizine 10mg", "Antihistamine", 400),
    ("Losartan 50mg", "Antihypertensive", 150), ("Aspirin 75mg", "Antiplatelet", 500),
    ("Clopidogrel 75mg", "Antiplatelet", 90), ("Insulin Glargine", "Antidiabetic", 12),
    ("Glimepiride 2mg", "Antidiabetic", 210), ("Levothyroxine 50mcg", "Thyroid", 175),
    ("Omeprazole 20mg", "Antacid", 280), ("Ciprofloxacin 500mg", "Antibiotic", 95),
    ("Doxycycline 100mg", "Antibiotic", 140), ("Prednisolone 10mg", "Steroid", 60),
    ("Dexamethasone 4mg", "Steroid", 8), ("Furosemide 40mg", "Diuretic", 130),
    ("Metoprolol 50mg", "Beta Blocker", 170), ("Enoxaparin 40mg", "Anticoagulant", 25),
    ("Heparin 5000IU", "Anticoagulant", 40), ("Morphine 10mg", "Opioid Analgesic", 15),
    ("Diclofenac 50mg", "Analgesic", 310), ("Ranitidine 150mg", "Antacid", 200),
    ("Domperidone 10mg", "Antiemetic", 185), ("Montelukast 10mg", "Anti-asthmatic", 115),
    ("Budesonide Inhaler", "Bronchodilator", 30), ("ORS Sachet", "Rehydration", 600),
    ("Normal Saline 500ml", "IV Fluid", 220), ("Ringer Lactate 500ml", "IV Fluid", 14),
    ("Vitamin B12 Injection", "Supplement", 75), ("Calcium 500mg", "Supplement", 340),
    ("Iron Folic Acid", "Supplement", 420), ("Zinc 20mg", "Supplement", 260),
    ("Cefixime 200mg", "Antibiotic", 100), ("Meropenem 1g IV", "Antibiotic (IV)", 20),
    ("Vancomycin 500mg IV", "Antibiotic (IV)", 16), ("Lorazepam 1mg", "Sedative", 45),
    ("Tramadol 50mg", "Analgesic", 85), ("Fluconazole 150mg", "Antifungal", 70),
    ("Acyclovir 400mg", "Antiviral", 65), ("Oseltamivir 75mg", "Antiviral", 55),
    ("Atenolol 50mg", "Beta Blocker", 160), ("Rosuvastatin 10mg", "Cardiovascular", 190),
]

# Ward layout: name, floor, bed-number prefix, number of beds -> 60 beds total
WARD_LAYOUT = [
    ("ICU", 3, "ICU", 10),
    ("General", 1, "GEN", 20),
    ("Pediatrics", 2, "PED", 12),
    ("Emergency", 0, "ER", 10),
    ("Maternity", 2, "MAT", 8),
]


def confirm_wipe(force: bool) -> bool:
    """Ask before deleting an existing database (skipped with --force)."""
    if force:
        return True
    try:
        answer = input("This will ERASE all existing HospitalOS data. Continue? [y/N] ")
    except EOFError:  # no keyboard attached (e.g. run from a script) -> be safe, don't wipe
        print("\nNo answer given. Use --force to seed without asking.")
        return False
    return answer.strip().lower() in ("y", "yes")


def make_phone() -> str:
    """Obviously-fake phone number (555 prefix)."""
    return f"555-{random.randint(1000, 9999)}"


def seed_database():
    """Drop all tables, recreate them, and insert synthetic data."""
    print("Resetting and creating HospitalOS database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        # ---- 1. Wards ----
        wards = [models.Ward(name=n, floor=f, capacity=c) for n, f, _, c in WARD_LAYOUT]
        db.add_all(wards)
        db.commit()
        ward_by_name = {w.name: w for w in wards}

        # ---- 2. Patients: 10 hand-written core patients, then 90 from Faker ----
        core = [  # name, age, gender, blood, diagnosis, admitted, created_ago
            ("Aarav Sharma", 58, "Male", "O+", "Acute Myocardial Infarction", True, timedelta(days=3)),
            ("Meera Nair", 34, "Female", "A+", "Community-Acquired Pneumonia", True, timedelta(days=2)),
            ("Rohan Verma", 27, "Male", "B+", "Viral Fever & Dehydration", False, timedelta(days=5)),
            ("Ananya Iyer", 8, "Female", "AB+", "Pediatric Asthma Exacerbation", True, timedelta(days=1)),
            ("Kabir Patel", 45, "Male", "O-", "Type 2 Diabetes Follow-up", False, timedelta(days=7)),
            ("Priya Deshmukh", 62, "Female", "A-", "Hypertensive Crisis", True, timedelta(hours=18)),
            ("Vikram Rao", 41, "Male", "B-", "Distal Radius Fracture", True, timedelta(hours=8)),
            ("Sanya Kapoor", 29, "Female", "O+", "Migraine with Aura", False, timedelta(days=4)),
            ("Devansh Joshi", 11, "Male", "A+", "Acute Gastroenteritis", False, timedelta(days=2)),
            ("Neha Kulkarni", 51, "Female", "AB-", "Post-Op Cholecystectomy", True, timedelta(days=2)),
        ]
        patients = [
            models.Patient(full_name=n, age=a, gender=g, phone=f"555-01{i:02d}", blood_group=b,
                           diagnosis=d, is_admitted=adm, created_at=now - ago)
            for i, (n, a, g, b, d, adm, ago) in enumerate(core, start=1)
        ]
        for _ in range(90):
            gender = random.choice(["Male", "Female"])
            name = fake.name_male() if gender == "Male" else fake.name_female()
            patients.append(models.Patient(
                full_name=name, age=random.randint(1, 90), gender=gender, phone=make_phone(),
                blood_group=random.choice(BLOOD_GROUPS), diagnosis=random.choice(DIAGNOSES),
                is_admitted=False, created_at=now - timedelta(days=random.randint(0, 60)),
            ))
        db.add_all(patients)
        db.commit()

        # ---- 3. Beds: 60 beds. Core patients get fixed beds, others filled randomly ----
        core_beds = {"ICU-01": 0, "ICU-02": 5, "GEN-01": 1, "GEN-02": 9, "PED-01": 3, "ER-01": 6}
        beds = []
        for ward_name, _, prefix, count in WARD_LAYOUT:
            for n in range(1, count + 1):
                beds.append(models.Bed(bed_number=f"{prefix}-{n:02d}", ward_id=ward_by_name[ward_name].id))
        bed_by_number = {b.bed_number: b for b in beds}

        def occupy(bed, patient):
            bed.is_occupied, bed.patient_id = True, patient.id
            bed.admitted_at = now - timedelta(hours=random.randint(2, 120))
            patient.is_admitted = True

        for number, idx in core_beds.items():
            occupy(bed_by_number[number], patients[idx])

        # Fill ~45% of the remaining beds with extra patients; keep ICU-03..05 free for demos
        keep_free = {"ICU-03", "ICU-04", "ICU-05", "ICU-06"}
        spare_patients = [p for p in patients[10:]]
        random.shuffle(spare_patients)
        for bed in beds:
            if bed.bed_number in core_beds or bed.bed_number in keep_free:
                continue
            if random.random() < 0.45 and spare_patients:
                occupy(bed, spare_patients.pop())
            elif random.random() < 0.3:  # previously used, now free
                bed.admitted_at = now - timedelta(days=random.randint(3, 9))
                bed.discharged_at = now - timedelta(days=random.randint(0, 2))
        db.add_all(beds)
        db.commit()

        # ---- 4. Doctors: 6 core + 9 generated = 15 ----
        core_docs = [
            ("Dr. Rajesh Menon", "Cardiology", "ICU", True),
            ("Dr. Sunita Reddy", "Internal Medicine", "General", True),
            ("Dr. Farhan Ali", "Pediatrics", "Pediatrics", True),
            ("Dr. Kavita Bose", "Emergency & Trauma", "Emergency", True),
            ("Dr. Siddharth Chatterjee", "Neurology", "General", False),
            ("Dr. Pooja Malhotra", "General Surgery", "General", True),
        ]
        doctors = [
            models.Doctor(full_name=n, specialization=s, phone=f"555-02{i:02d}",
                          ward_id=ward_by_name[w].id, is_available=av)
            for i, (n, s, w, av) in enumerate(core_docs, start=1)
        ]
        for spec in random.sample(SPECIALIZATIONS, 9):
            doctors.append(models.Doctor(
                full_name=f"Dr. {fake.name()}", specialization=spec, phone=make_phone(),
                ward_id=random.choice(wards).id, is_available=random.random() < 0.85,
            ))
        db.add_all(doctors)
        db.commit()

        # ---- 5. Appointments: 6 core + 54 generated = 60 ----
        appointments = [
            models.Appointment(patient_id=patients[0].id, doctor_id=doctors[0].id,
                               appointment_time=now + timedelta(hours=2), status="Scheduled",
                               notes="Post-angioplasty ICU cardiac evaluation"),
            models.Appointment(patient_id=patients[2].id, doctor_id=doctors[1].id,
                               appointment_time=now - timedelta(days=1), status="Completed",
                               notes="Outpatient recovery checkup"),
            models.Appointment(patient_id=patients[3].id, doctor_id=doctors[2].id,
                               appointment_time=now + timedelta(hours=4), status="Scheduled",
                               notes="Nebulization response review"),
            models.Appointment(patient_id=patients[4].id, doctor_id=doctors[1].id,
                               appointment_time=now + timedelta(days=1), status="Scheduled",
                               notes="Quarterly HbA1c review"),
            models.Appointment(patient_id=patients[7].id, doctor_id=doctors[4].id,
                               appointment_time=now - timedelta(days=2), status="Cancelled",
                               notes="Rescheduled at patient request"),
            models.Appointment(patient_id=patients[9].id, doctor_id=doctors[5].id,
                               appointment_time=now + timedelta(hours=6), status="Scheduled",
                               notes="Surgical dressing inspection"),
        ]
        taken = {(a.doctor_id, a.appointment_time.replace(minute=0, second=0, microsecond=0)) for a in appointments}
        while len(appointments) < 60:
            doc = random.choice(doctors)
            day_offset = random.randint(-10, 10)
            when = (now + timedelta(days=day_offset)).replace(
                hour=random.randint(9, 16), minute=0, second=0, microsecond=0)
            if (doc.id, when) in taken:  # never double-book a doctor
                continue
            taken.add((doc.id, when))
            if day_offset < 0:
                status = random.choices(["Completed", "Cancelled"], weights=[8, 2])[0]
            else:
                status = random.choices(["Scheduled", "Cancelled"], weights=[9, 1])[0]
            appointments.append(models.Appointment(
                patient_id=random.choice(patients).id, doctor_id=doc.id,
                appointment_time=when, status=status, notes=random.choice(DIAGNOSES) + " consult"))
        db.add_all(appointments)
        db.commit()

        # ---- 6. Medicines: 8 core + 42 extra = 50 (some low stock on purpose) ----
        medicines = [
            models.Medicine(name="Amoxicillin 500mg", category="Antibiotic", stock_quantity=240, unit_price=1.50, expiry_date="2027-08-15"),
            models.Medicine(name="Paracetamol 650mg", category="Analgesic / Antipyretic", stock_quantity=520, unit_price=0.40, expiry_date="2027-11-30"),
            models.Medicine(name="Atorvastatin 20mg", category="Cardiovascular", stock_quantity=180, unit_price=2.20, expiry_date="2027-05-20"),
            models.Medicine(name="Salbutamol Inhaler", category="Bronchodilator", stock_quantity=45, unit_price=8.75, expiry_date="2027-04-10"),
            models.Medicine(name="Metformin 500mg", category="Antidiabetic", stock_quantity=310, unit_price=0.85, expiry_date="2028-01-15"),
            models.Medicine(name="Amlodipine 5mg", category="Antihypertensive", stock_quantity=195, unit_price=1.10, expiry_date="2027-09-01"),
            models.Medicine(name="Ceftriaxone 1g IV", category="Antibiotic (IV)", stock_quantity=18, unit_price=6.50, expiry_date="2027-02-28"),
            models.Medicine(name="Ondansetron 4mg", category="Antiemetic", stock_quantity=140, unit_price=1.25, expiry_date="2027-10-12"),
        ]
        for name, category, stock in EXTRA_MEDICINES:
            expiry = (now + timedelta(days=random.randint(60, 900))).strftime("%Y-%m-%d")
            medicines.append(models.Medicine(
                name=name, category=category, stock_quantity=stock,
                unit_price=round(random.uniform(0.3, 25.0), 2), expiry_date=expiry))
        db.add_all(medicines)
        db.commit()

        # ---- 7. Lab tests: 6 core + 44 generated = 50 ----
        lab_rows = [
            (0, 0, "Troponin-I & Lipid Profile", "Completed", "Troponin-I elevated (1.8 ng/mL); LDL 148 mg/dL", timedelta(days=2)),
            (1, 1, "Chest X-Ray & Complete Blood Count", "Completed", "Right lower lobe consolidation; WBC 13,400 /uL", timedelta(days=1, hours=12)),
            (3, 2, "Pulse Oximetry & Spirometry", "Completed", "SpO2 96% on room air after bronchodilator", timedelta(hours=18)),
            (4, 1, "HbA1c & Fasting Blood Glucose", "Pending", None, timedelta(hours=5)),
            (5, 0, "Renal Function Panel & ECG", "Pending", None, timedelta(hours=3)),
            (6, 3, "Right Wrist AP/Lateral Radiograph", "Completed", "Non-displaced distal radius fracture confirmed", timedelta(hours=6)),
        ]
        lab_tests = [
            models.LabTest(patient_id=patients[p].id, doctor_id=doctors[d].id, test_name=t,
                           status=s, result=r, ordered_at=now - ago)
            for p, d, t, s, r, ago in lab_rows
        ]
        for _ in range(44):
            done = random.random() < 0.6
            lab_tests.append(models.LabTest(
                patient_id=random.choice(patients).id, doctor_id=random.choice(doctors).id,
                test_name=random.choice(LAB_TESTS), status="Completed" if done else "Pending",
                result=random.choice(LAB_RESULTS) if done else None,
                ordered_at=now - timedelta(hours=random.randint(1, 240))))
        db.add_all(lab_tests)
        db.commit()

        # ---- 8. Bills: 6 core + 64 generated = 70 ----
        bill_rows = [
            (0, 1450.00, "Partial", "ICU Bed (3 days), Cardiac Monitoring, Troponin-I Lab", timedelta(days=1)),
            (1, 420.00, "Unpaid", "General Ward Bed (2 days), IV Antibiotics, Chest X-Ray", timedelta(hours=20)),
            (2, 85.00, "Paid", "Outpatient Consultation & Oral Rehydration Pack", timedelta(days=2)),
            (3, 310.00, "Unpaid", "Pediatrics Bed (1 day), Nebulization Therapy", timedelta(hours=10)),
            (6, 275.00, "Paid", "Emergency Cast Application & Wrist X-Ray", timedelta(hours=4)),
            (9, 980.00, "Unpaid", "Laparoscopic Cholecystectomy & General Ward Recovery", timedelta(days=1)),
        ]
        bills = [
            models.Bill(patient_id=patients[p].id, total_amount=amt, paid_status=st,
                        description=desc, created_at=now - ago)
            for p, amt, st, desc, ago in bill_rows
        ]
        for _ in range(64):
            bills.append(models.Bill(
                patient_id=random.choice(patients).id,
                total_amount=round(random.uniform(40, 2500), 2),
                paid_status=random.choices(["Paid", "Unpaid", "Partial"], weights=[5, 3, 2])[0],
                description=", ".join(random.sample(BILL_ITEMS, 3)),
                created_at=now - timedelta(days=random.randint(0, 30))))
        db.add_all(bills)
        db.commit()

        occupied = sum(1 for b in beds if b.is_occupied)
        print("Successfully seeded HospitalOS database with synthetic records!")
        print(f"  - {len(wards)} Wards, {len(beds)} Beds ({occupied} occupied, {len(beds) - occupied} free)")
        print(f"  - {len(patients)} Patients, {len(doctors)} Doctors, {len(appointments)} Appointments")
        print(f"  - {len(medicines)} Medicines, {len(lab_tests)} Lab Tests, {len(bills)} Bills")

    finally:
        db.close()


if __name__ == "__main__":
    if confirm_wipe("--force" in sys.argv):
        seed_database()
    else:
        print("Cancelled. Nothing was changed.")
