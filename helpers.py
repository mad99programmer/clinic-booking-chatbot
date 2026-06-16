from crud import (
    get_available_sessions,
    get_available_slots
)

def paginate_slots(
    slots,
    page,
    page_size=8
):
    start = page * page_size
    end = start + page_size

    return slots[start:end]

def extract_payload(webhook_data):
    if not webhook_data:
        return None

    metadata = webhook_data.get("metadata", {})

    return metadata.get("interactiveId")


def get_slots_for_selected_session(
    db,
    doctor_id,
    selected_date,
    selected_session_index
):
    sessions = get_available_sessions(
        db,
        doctor_id,
        selected_date
    )

    selected_session = sessions[
        selected_session_index
    ]

    all_slots = get_available_slots(
        db,
        doctor_id,
        selected_date
    )

    slots = []

    for slot in all_slots:

        if (
            slot.start_time >= selected_session["start"]
            and
            slot.end_time <= selected_session["end"]
        ):
            slots.append(slot)

    return slots

def has_next_page(
    slots,
    page,
    page_size=9
):
    return (page + 1) * page_size < len(slots)

def has_previous_page(page):
    return page > 0