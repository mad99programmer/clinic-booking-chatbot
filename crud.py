from models import Doctor, DoctorSlot


# =========================
# FETCH SPECIALIZATIONS
# =========================
def get_specializations(db):

    specializations = db.query(
        Doctor.specialization
    ).distinct().all()

    return [s[0] for s in specializations]


# =========================
# FETCH DOCTORS BASED ON SELECTED SPECIALIZATION
# =========================
def get_doctors_by_specialization(db, specialization):

    return db.query(Doctor).filter(
        Doctor.specialization == specialization,
        Doctor.is_active == True
    ).all()


# =========================
# GET AVAILABLE DATES FOR THE SELECTED DOCTOR
# =========================
def get_available_dates(db, doctor_id):

    slots = db.query(
        DoctorSlot.slot_date
    ).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == "available"
    ).distinct().all()

    return [slot[0] for slot in slots]


# =========================
# GET AVAILABLE SLOTS FOR THE SELECTED DOCTOR AND DATE
# =========================
def get_available_slots(db, doctor_id, slot_date):

    return db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.slot_date == slot_date,
        DoctorSlot.status == "available"
    ).all()