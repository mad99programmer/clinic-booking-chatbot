# slot_generator.py

from datetime import datetime, timedelta, date

from database import SessionLocal

from models import (
    Doctor,
    DoctorAvailability,
    DoctorLeave,
    DoctorSlot
)


# =========================
# DB SESSION
# =========================
db = SessionLocal()


# =========================
# GENERATE SLOTS
# =========================
def generate_slots_for_next_7_days():

    today = date.today()

    for day_offset in range(7):

        current_date    = today + timedelta(days=day_offset)
        current_weekday = current_date.strftime("%A")

        # fetch matching availability
        availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.weekday   == current_weekday,
            DoctorAvailability.is_active == True
        ).all()

        for availability in availabilities:

            doctor = db.query(Doctor).filter(
                Doctor.id       == availability.doctor_id,
                Doctor.is_active == True          # skip inactive doctors
            ).first()

            if not doctor:
                continue

            # ── skip if doctor is on leave ──
            on_leave = db.query(DoctorLeave).filter(
                DoctorLeave.doctor_id  == doctor.id,
                DoctorLeave.leave_date == current_date
            ).first()

            if on_leave:
                print(
                    f"⏭️  Skipping {doctor.name} on "
                    f"{current_date} — on leave"
                )
                continue

            duration = doctor.consultation_duration

            start_datetime = datetime.combine(
                current_date,
                availability.start_time
            )
            end_datetime = datetime.combine(
                current_date,
                availability.end_time
            )

            current_slot = start_datetime

            while current_slot < end_datetime:

                next_slot = current_slot + timedelta(minutes=duration)

                if next_slot > end_datetime:
                    break

                # avoid duplicates
                existing = db.query(DoctorSlot).filter(
                    DoctorSlot.doctor_id  == doctor.id,
                    DoctorSlot.slot_date  == current_date,
                    DoctorSlot.start_time == current_slot.time()
                ).first()

                if not existing:
                    slot = DoctorSlot(
                        doctor_id=doctor.id,
                        availability_id=availability.id,
                        slot_date=current_date,
                        start_time=current_slot.time(),
                        end_time=next_slot.time(),
                        status="available"
                    )
                    db.add(slot)

                current_slot = next_slot

    db.commit()
    print("✅ Slots generated successfully!")


# =========================
# RUN
# =========================
generate_slots_for_next_7_days()