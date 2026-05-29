# =========================
# admin_routes.py
# =========================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, time, timedelta, datetime

from database import SessionLocal
from models import User, Doctor, DoctorSlot, DoctorAvailability, Appointment,DoctorLeave


router = APIRouter(prefix="/admin", tags=["admin"])


# =========================
# DATABASE SESSION
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# PYDANTIC SCHEMAS
# =========================

class DoctorCreate(BaseModel):
    name: str
    specialization: str
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[int] = None
    consultation_duration: int = 30
    phone: Optional[str] = None
    email: Optional[str] = None


class DoctorUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[int] = None
    consultation_duration: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class SlotCreate(BaseModel):
    doctor_id: int
    availability_id: int
    slot_date: date
    start_time: time
    end_time: time


class SlotBulkCreate(BaseModel):
    doctor_id: int
    availability_id: int
    from_date: date
    to_date: date
    start_time: time
    end_time: time
    slot_duration_minutes: int = 20
    skip_sundays: bool = True

# =========================
# AVAILABILITY SCHEMAS
# =========================
 
class AvailabilityCreate(BaseModel):
    weekday: str
    start_time: time
    end_time: time



# =========================
# LEAVE SCHEMA
# =========================
 
class LeaveCreate(BaseModel):
    leave_date: date
    reason: Optional[str] = None
 
# =========================
# DASHBOARD — STATS
# =========================
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):

    today = date.today()

    total_patients = db.query(User).count()

    total_doctors = db.query(Doctor).filter(
        Doctor.is_active == True
    ).count()

    appointments_today = db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).count()

    open_slots = db.query(DoctorSlot).filter(
        DoctorSlot.status == "available",
        DoctorSlot.slot_date >= today
    ).count()

    total_appointments = db.query(Appointment).count()

    return {
        "total_patients":     total_patients,
        "total_doctors":      total_doctors,
        "appointments_today": appointments_today,
        "open_slots":         open_slots,
        "total_appointments": total_appointments,
    }


# =========================
# DASHBOARD — TODAY'S APPOINTMENTS
# =========================
@router.get("/appointments/today")
def get_today_appointments(db: Session = Depends(get_db)):

    today = date.today()

    appointments = db.query(Appointment).filter(
        Appointment.appointment_date == today
    ).all()

    result = []

    for appt in appointments:

        user = db.query(User).filter(
            User.id == appt.user_id
        ).first()

        doctor = db.query(Doctor).filter(
            Doctor.id == appt.doctor_id
        ).first()

        slot = db.query(DoctorSlot).filter(
            DoctorSlot.id == appt.slot_id
        ).first()

        result.append({
            "id":             appt.id,
            "patient_name":   user.name         if user   else "Unknown",
            "patient_phone":  user.phone_number if user   else "",
            "patient_age":    user.age          if user   else None,
            "doctor_name":    doctor.name       if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "",
            "date":           str(appt.appointment_date),
            "time":           slot.start_time.strftime("%I:%M %p") if slot else "",
            "status":         appt.status,
            "notes":          appt.notes or "",
        })

    return result


# =========================
# APPOINTMENTS — ALL (with filters)
# =========================
@router.get("/appointments")
def get_all_appointments(
    doctor_id: Optional[int]  = None,
    status:    Optional[str]  = None,
    from_date: Optional[date] = None,
    to_date:   Optional[date] = None,
    db: Session = Depends(get_db)
):

    query = db.query(Appointment)

    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)

    if status:
        query = query.filter(Appointment.status == status)

    if from_date:
        query = query.filter(Appointment.appointment_date >= from_date)

    if to_date:
        query = query.filter(Appointment.appointment_date <= to_date)

    appointments = query.order_by(
        Appointment.appointment_date.desc()
    ).all()

    result = []

    for appt in appointments:

        user = db.query(User).filter(
            User.id == appt.user_id
        ).first()

        doctor = db.query(Doctor).filter(
            Doctor.id == appt.doctor_id
        ).first()

        slot = db.query(DoctorSlot).filter(
            DoctorSlot.id == appt.slot_id
        ).first()

        result.append({
            "id":             appt.id,
            "patient_name":   user.name         if user   else "Unknown",
            "patient_phone":  user.phone_number if user   else "",
            "patient_email":  user.email        if user   else "",
            "patient_age":    user.age          if user   else None,
            "doctor_name":    doctor.name       if doctor else "Unknown",
            "specialization": doctor.specialization if doctor else "",
            "date":           str(appt.appointment_date),
            "time":           slot.start_time.strftime("%I:%M %p") if slot else "",
            "status":         appt.status,
            "notes":          appt.notes or "",
        })

    return result


# =========================
# APPOINTMENTS — CANCEL
# =========================
@router.put("/appointments/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:
        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400,
            detail="Already cancelled"
        )

    # free up the slot
    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == appointment.slot_id
    ).first()

    if slot:
        slot.status = "available"

    appointment.status = "cancelled"

    db.commit()

    return {"message": "Appointment cancelled successfully"}


# =========================
# DOCTORS — LIST
# =========================
@router.get("/doctors")
def get_doctors(db: Session = Depends(get_db)):

    doctors = db.query(Doctor).all()

    result = []

    for doctor in doctors:

        available_slots = db.query(DoctorSlot).filter(
            DoctorSlot.doctor_id == doctor.id,
            DoctorSlot.status == "available",
            DoctorSlot.slot_date >= date.today()
        ).count()

        total_appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id
        ).count()

        result.append({
            "id":                   doctor.id,
            "name":                 doctor.name,
            "specialization":       doctor.specialization,
            "qualification":        doctor.qualification       or "",
            "experience_years":     doctor.experience_years    or 0,
            "consultation_fee":     doctor.consultation_fee    or 0,
            "consultation_duration":doctor.consultation_duration,
            "phone":                doctor.phone               or "",
            "email":                doctor.email               or "",
            "is_active":            doctor.is_active,
            "available_slots":      available_slots,
            "total_appointments":   total_appointments,
        })

    return result


# =========================
# DOCTORS — ADD
# =========================
@router.post("/doctors")
def add_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db)
):

    doctor = Doctor(
        name=payload.name,
        specialization=payload.specialization,
        qualification=payload.qualification,
        experience_years=payload.experience_years,
        consultation_fee=payload.consultation_fee,
        consultation_duration=payload.consultation_duration,
        phone=payload.phone,
        email=payload.email,
        is_active=True
    )

    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    return {
        "message": "Doctor added successfully",
        "id": doctor.id
    }


# =========================
# DOCTORS — EDIT / DEACTIVATE
# =========================
@router.put("/doctors/{doctor_id}")
def update_doctor(
    doctor_id: int,
    payload: DoctorUpdate,
    db: Session = Depends(get_db)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    if payload.name                  is not None: doctor.name                  = payload.name
    if payload.specialization        is not None: doctor.specialization        = payload.specialization
    if payload.qualification         is not None: doctor.qualification         = payload.qualification
    if payload.experience_years      is not None: doctor.experience_years      = payload.experience_years
    if payload.consultation_fee      is not None: doctor.consultation_fee      = payload.consultation_fee
    if payload.consultation_duration is not None: doctor.consultation_duration = payload.consultation_duration
    if payload.phone                 is not None: doctor.phone                 = payload.phone
    if payload.email                 is not None: doctor.email                 = payload.email
    if payload.is_active             is not None: doctor.is_active             = payload.is_active

    db.commit()

    return {"message": "Doctor updated successfully"}


# =========================
# SLOTS — LIST
# =========================
@router.get("/slots")
def get_slots(
    doctor_id: Optional[int]  = None,
    slot_date: Optional[date] = None,
    status:    Optional[str]  = None,
    db: Session = Depends(get_db)
):

    query = db.query(DoctorSlot)

    if doctor_id:
        query = query.filter(DoctorSlot.doctor_id == doctor_id)

    if slot_date:
        query = query.filter(DoctorSlot.slot_date == slot_date)

    if status:
        query = query.filter(DoctorSlot.status == status)

    slots = query.order_by(
        DoctorSlot.slot_date,
        DoctorSlot.start_time
    ).all()

    result = []

    for slot in slots:

        doctor = db.query(Doctor).filter(
            Doctor.id == slot.doctor_id
        ).first()

        result.append({
            "id":              slot.id,
            "doctor_id":       slot.doctor_id,
            "doctor_name":     doctor.name if doctor else "Unknown",
            "availability_id": slot.availability_id,
            "date":            str(slot.slot_date),
            "start_time":      slot.start_time.strftime("%I:%M %p"),
            "end_time":        slot.end_time.strftime("%I:%M %p"),
            "status":          slot.status,
        })

    return result


# =========================
# SLOTS — ADD SINGLE
# =========================
@router.post("/slots")
def add_slot(
    payload: SlotCreate,
    db: Session = Depends(get_db)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == payload.doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == payload.availability_id
    ).first()

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability record not found"
        )

    slot = DoctorSlot(
        doctor_id=payload.doctor_id,
        availability_id=payload.availability_id,
        slot_date=payload.slot_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="available"
    )

    db.add(slot)
    db.commit()

    return {"message": "Slot added successfully"}


# =========================
# SLOTS — BULK ADD
# =========================
@router.post("/slots/bulk")
def add_slots_bulk(
    payload: SlotBulkCreate,
    db: Session = Depends(get_db)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == payload.doctor_id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == payload.availability_id
    ).first()

    if not availability:
        raise HTTPException(
            status_code=404,
            detail="Availability record not found"
        )

    created = 0
    current_date = payload.from_date
    duration = timedelta(minutes=payload.slot_duration_minutes)

    while current_date <= payload.to_date:

        # skip sundays if requested
        if payload.skip_sundays and current_date.weekday() == 6:
            current_date += timedelta(days=1)
            continue

        current_start = datetime.combine(current_date, payload.start_time)
        end_limit     = datetime.combine(current_date, payload.end_time)

        while current_start + duration <= end_limit:

            slot = DoctorSlot(
                doctor_id=payload.doctor_id,
                availability_id=payload.availability_id,
                slot_date=current_date,
                start_time=current_start.time(),
                end_time=(current_start + duration).time(),
                status="available"
            )

            db.add(slot)
            created += 1

            current_start += duration

        current_date += timedelta(days=1)

    db.commit()

    return {
        "message": f"{created} slots created successfully",
        "slots_created": created
    }


# =========================
# SLOTS — DELETE
# =========================
@router.delete("/slots/{slot_id}")
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db)
):

    slot = db.query(DoctorSlot).filter(
        DoctorSlot.id == slot_id
    ).first()

    if not slot:
        raise HTTPException(
            status_code=404,
            detail="Slot not found"
        )

    if slot.status == "booked":
        raise HTTPException(
            status_code=400,
            detail="Cannot delete a booked slot. Cancel the appointment first."
        )

    db.delete(slot)
    db.commit()

    return {"message": "Slot deleted successfully"}


# =========================
# PATIENTS — LIST
# =========================
@router.get("/patients")
def get_patients(db: Session = Depends(get_db)):

    patients = db.query(User).all()

    result = []

    for patient in patients:

        total_appointments = db.query(Appointment).filter(
            Appointment.user_id == patient.id
        ).count()

        last_appointment = db.query(Appointment).filter(
            Appointment.user_id == patient.id
        ).order_by(
            Appointment.appointment_date.desc()
        ).first()

        result.append({
            "id":                 patient.id,
            "name":               patient.name,
            "phone":              patient.phone_number,
            "email":              patient.email  or "",
            "gender":             patient.gender or "",
            "age":                patient.age    or None,
            "total_appointments": total_appointments,
            "last_appointment":   str(last_appointment.appointment_date)
                                  if last_appointment else None,
            "registered_at":      str(patient.created_at.date())
                                  if patient.created_at else "",
        })

    return result


# =========================
# AVAILABILITY — GET FOR DOCTOR
# =========================
@router.get("/doctors/{doctor_id}/availability")
def get_doctor_availability(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
 
    availabilities = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id
    ).all()
 
    return [
        {
            "id":         a.id,
            "weekday":    a.weekday,
            "start_time": a.start_time.strftime("%H:%M"),
            "end_time":   a.end_time.strftime("%H:%M"),
            "is_active":  a.is_active,
        }
        for a in availabilities
    ]
 
 
# =========================
# AVAILABILITY — ADD FOR DOCTOR
# =========================
@router.post("/doctors/{doctor_id}/availability")
def add_doctor_availability(
    doctor_id: int,
    payload: AvailabilityCreate,
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
 
    # prevent duplicate weekday entry
    existing = db.query(DoctorAvailability).filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.weekday == payload.weekday,
        DoctorAvailability.is_active == True
    ).first()
 
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Availability for {payload.weekday} already exists"
        )
 
    availability = DoctorAvailability(
        doctor_id=doctor_id,
        weekday=payload.weekday,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_active=True
    )
 
    db.add(availability)
    db.commit()
    db.refresh(availability)
 
    return {
        "message": "Availability added successfully",
        "id": availability.id
    }
 
 
# =========================
# AVAILABILITY — DELETE
# =========================
@router.delete("/availability/{availability_id}")
def delete_availability(
    availability_id: int,
    db: Session = Depends(get_db)
):
    availability = db.query(DoctorAvailability).filter(
        DoctorAvailability.id == availability_id
    ).first()
 
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
 
    db.delete(availability)
    db.commit()
 
    return {"message": "Availability deleted successfully"}


# =========================
# LEAVE — GET FOR DOCTOR
# =========================
@router.get("/doctors/{doctor_id}/leave")
def get_doctor_leaves(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
 
    leaves = db.query(DoctorLeave).filter(
        DoctorLeave.doctor_id == doctor_id,
        DoctorLeave.leave_date >= date.today()
    ).order_by(DoctorLeave.leave_date).all()
 
    return [
        {
            "id":         l.id,
            "leave_date": str(l.leave_date),
            "reason":     l.reason or "",
        }
        for l in leaves
    ]
 
 
# =========================
# LEAVE — MARK LEAVE
# handles: cancel booked appointments + notify patients + delete available slots
# =========================
@router.post("/doctors/{doctor_id}/leave")
@router.post("/doctors/{doctor_id}/leave")
def mark_leave(
    doctor_id: int,
    payload: LeaveCreate,
    db: Session = Depends(get_db)
):
    from messaging import send_reply

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    existing = db.query(DoctorLeave).filter(
        DoctorLeave.doctor_id  == doctor_id,
        DoctorLeave.leave_date == payload.leave_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Leave already marked for this date")

    # cancel booked appointments + notify patients
    booked = db.query(Appointment).filter(
        Appointment.doctor_id        == doctor_id,
        Appointment.appointment_date == payload.leave_date,
        Appointment.status           == "booked"
    ).all()

    cancelled_count = 0
    for appt in booked:
        appt.status = "cancelled"
        patient = db.query(User).filter(User.id == appt.user_id).first()
        if patient:
            formatted_date = payload.leave_date.strftime("%d %B %Y")
            msg = (
                f"Dear {patient.name},\n\n"
                f"Your appointment with Dr. {doctor.name} on "
                f"{formatted_date} has been cancelled due to doctor unavailability.\n\n"
                f"Reply *hi* to rebook."
            )
            try:
                send_reply(patient.phone_number, msg)
            except Exception:
                pass
        cancelled_count += 1

    # mark available slots as cancelled — no deletion, avoids FK violation
    db.query(DoctorSlot).filter(
        DoctorSlot.doctor_id == doctor_id,
        DoctorSlot.slot_date == payload.leave_date,
        DoctorSlot.status    == "available"
    ).update({"status": "cancelled"})

    # save leave record
    leave = DoctorLeave(
        doctor_id  = doctor_id,
        leave_date = payload.leave_date,
        reason     = payload.reason
    )
    db.add(leave)
    db.commit()

    return {
        "message":                "Leave marked successfully",
        "cancelled_appointments": cancelled_count,
        "patients_notified":      cancelled_count,
    }