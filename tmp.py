from datetime import datetime, timedelta, date

from database import SessionLocal
from models import Doctor, DoctorAvailability, DoctorSlot


db = SessionLocal()
today = date.today()
print(today)

current_date = today + timedelta(days=2)
print(current_date)

current_weekday = current_date.strftime("%A")
print(current_weekday)

availabilities = db.query(DoctorAvailability).filter(
            DoctorAvailability.weekday == current_weekday,
            DoctorAvailability.is_active == True
        ).all()
print(availabilities)

for availability in availabilities:
    print(availability)
    doctor = db.query(Doctor).filter(
                Doctor.id == availability.doctor_id
            ).first()
    print(doctor.name)
    duration = doctor.consultation_duration

    start_datetime = datetime.combine(
                current_date,
                availability.start_time
            )

    end_datetime = datetime.combine(
                current_date,
                availability.end_time
            )
    print(start_datetime)
    print(end_datetime)
