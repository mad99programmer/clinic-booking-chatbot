# slot_generator.py

from datetime import datetime, timedelta, date

from database import SessionLocal

from models import (
    Doctor,
    DoctorAvailability,
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

    # next 7 days
    for day_offset in range(7):

        current_date = today + timedelta(days=day_offset)

        current_weekday = current_date.strftime("%A")

        # fetch matching availability
        availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.weekday == current_weekday,
            DoctorAvailability.is_active == True
        ).all()

        # process each doctor schedule
        for availability in availabilities:

            doctor = db.query(Doctor).filter(
                Doctor.id == availability.doctor_id
            ).first()

            duration = doctor.consultation_duration

            # combine date + time
            start_datetime = datetime.combine(
                current_date,
                availability.start_time
            )

            end_datetime = datetime.combine(
                current_date,
                availability.end_time
            )

            current_slot = start_datetime

            # generate slots
            while current_slot < end_datetime:

                next_slot = current_slot + timedelta(
                    minutes=duration
                )

                # prevent overflow
                if next_slot > end_datetime:
                    break

                # avoid duplicate slots
                existing_slot = db.query(DoctorSlot).filter(
                    DoctorSlot.doctor_id == doctor.id,
                    DoctorSlot.slot_date == current_date,
                    DoctorSlot.start_time == current_slot.time()
                ).first()

                # create slot if not exists
                if not existing_slot:

                    slot = DoctorSlot(
                        doctor_id=doctor.id,
                        availability_id=availability.id,
                        slot_date=current_date,
                        start_time=current_slot.time(),
                        end_time=next_slot.time(),
                        status="available"
                    )

                    db.add(slot)

                # move to next interval
                current_slot = next_slot

    db.commit()

    print("✅ Slots generated successfully!")


# =========================
# RUN SCRIPT
# =========================
generate_slots_for_next_7_days()