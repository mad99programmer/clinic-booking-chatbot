from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    Date,
    Time,
    DateTime
)

from sqlalchemy.sql import func

from database import Base


# =========================
# USERS / PATIENTS
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)       # add this
    gender = Column(String, nullable=True)      # add this
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# =========================
# CHATBOT SESSION STATE
# =========================
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    phone_number = Column(
        String,
        unique=True,
        nullable=False
    )

    current_step = Column(
        String,
        default="idle"
    )
    temp_name = Column(String, nullable=True)
    # in UserSession model
    temp_email = Column(String, nullable=True)
    temp_gender = Column(String, nullable=True)

    selected_specialization = Column(
        String,
        nullable=True
    )

    selected_doctor_id = Column(
        Integer,
        nullable=True
    )

    selected_slot_id = Column(
        Integer,
        nullable=True
    )
    selected_date = Column(Date, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# =========================
# DOCTORS
# =========================
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    specialization = Column(String, nullable=False)

    qualification = Column(String, nullable=True)

    experience_years = Column(Integer, nullable=True)

    consultation_fee = Column(Integer, nullable=True)

    consultation_duration = Column(
        Integer,
        nullable=False,
        default=30
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# =========================
# DOCTOR WEEKLY AVAILABILITY
# =========================
class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    weekday = Column(
        String,
        nullable=False
    )

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# =========================
# GENERATED SLOTS
# =========================
class DoctorSlot(Base):
    __tablename__ = "doctor_slots"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    availability_id = Column(
        Integer,
        ForeignKey("doctor_availability.id"),
        nullable=False
    )

    slot_date = Column(
        Date,
        nullable=False
    )

    start_time = Column(
        Time,
        nullable=False
    )

    end_time = Column(
        Time,
        nullable=False
    )

    status = Column(
        String,
        default="available"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


# =========================
# APPOINTMENTS
# =========================
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False
    )

    slot_id = Column(
        Integer,
        ForeignKey("doctor_slots.id"),
        nullable=False
    )

    appointment_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String,
        default="booked"
    )

    notes = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )