from models import Doctor, DoctorSlot
from datetime import date, datetime, time

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
from datetime import date, datetime

def get_available_dates(db, doctor_id):

    query = db.query(
        DoctorSlot.slot_date
    ).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.status == "available"
    )

    today = date.today()
    now = datetime.now().time()

    dates = []

    distinct_dates = query.distinct().all()

    for row in distinct_dates:

        slot_date = row[0]

        # Future dates are always valid
        if slot_date > today:
            dates.append(slot_date)
            continue

        # Past dates should never appear
        if slot_date < today:
            continue

        # Today: check if any future slot exists
        future_slot_exists = db.query(
            DoctorSlot.id
        ).filter(
            DoctorSlot.doctor_id == doctor_id,
            DoctorSlot.slot_date == today,
            DoctorSlot.status == "available",
            DoctorSlot.start_time > now
        ).first()

        if future_slot_exists:
            dates.append(slot_date)

    return sorted(dates)
# =========================
# GET AVAILABLE SLOTS FOR THE SELECTED DOCTOR AND DATE
# =========================
def get_available_slots(db, doctor_id, slot_date):
 
    
 
    query = db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.slot_date == slot_date,
        DoctorSlot.status    == "available"
    )
 
    # if today — filter out slots that already passed
    if slot_date == date.today():
        now = datetime.now().time()
        query = query.filter(DoctorSlot.start_time > now)
 
    return query.order_by(DoctorSlot.start_time).all()


# =========================
# GET AVAILABLE SESSIONS
# =========================
def get_available_sessions(
    db,
    doctor_id,
    slot_date
):
    slots = get_available_slots(
        db,
        doctor_id,
        slot_date
    )

    if not slots:
        return []

    sessions = []

    current_start = slots[0].start_time
    previous_end = slots[0].end_time

    for slot in slots[1:]:

        if slot.start_time != previous_end:

            sessions.append({
                "start": current_start,
                "end": previous_end
            })

            current_start = slot.start_time

        previous_end = slot.end_time

    sessions.append({
        "start": current_start,
        "end": previous_end
    })

    return sessions