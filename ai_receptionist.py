import re
import ollama


VALID_SPECIALIZATIONS = [
    "Cardiologist",
    "Dentist",
    "Dermatologist",
    "Ophthalmologist",
    "Orthopedist",
    "Gastroenterologist",
    "Psychiatrist",
    "ENT Specialist",
    "Urologist",
    "Endocrinologist",
    "Neurologist",
    "Oncologist",
    "General Physician"
]


PRIORITY_ORDER = [
    "Cardiologist",
    "Neurologist",
    "Oncologist",
    "Orthopedist",
    "Gastroenterologist",
    "Dentist",
    "Dermatologist",
    "Ophthalmologist",
    "Psychiatrist",
    "ENT Specialist",
    "Urologist",
    "Endocrinologist",
    "General Physician"
]


def load_prompt():

    with open(
        "prompts/receptionist_prompt.txt",
        "r",
        encoding="utf-8"
    ) as file:

        return file.read()


def clean_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-zA-Z0-9,\s]",
        "",
        text
    )

    return text


def extract_specializations(raw_output):

    raw_output = clean_text(raw_output)

    detected = []

    for specialization in VALID_SPECIALIZATIONS:

        if specialization.lower() in raw_output:

            detected.append(
                specialization
            )

    return detected


def choose_highest_priority(
    detected_specializations
):

    for specialization in PRIORITY_ORDER:

        if specialization in detected_specializations:
            return specialization

    return "General Physician"


def ask_llm(symptoms):

    prompt_template = load_prompt()

    prompt = prompt_template.format(
        symptoms=symptoms
    )

    response = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    raw_output = (
        response["message"]["content"]
        .strip()
    )

    print("\nRAW MODEL OUTPUT:")
    print(raw_output)

    return raw_output


def generate_message(
    ideal_specialization,
    assigned_specialization
):

    if (
        ideal_specialization
        ==
        assigned_specialization
    ):

        return (
            f"We have a specialist available. "
            f"Please consult our "
            f"{assigned_specialization}."
        )

    return (
        f"Your symptoms suggest you may need "
        f"{ideal_specialization}, which is "
        f"currently unavailable. "
        f"Our General Physician can "
        f"evaluate you first."
    )


def suggest_specialization(
    symptoms,
    available_specializations
):

    raw_output = ask_llm(
        symptoms
    )

    detected_specializations = (
        extract_specializations(
            raw_output
        )
    )

    print(
        "\nDETECTED SPECIALIZATIONS:"
    )

    print(
        detected_specializations
    )

    ideal_specialization = (
        choose_highest_priority(
            detected_specializations
        )
    )

    if (
        ideal_specialization
        in
        available_specializations
    ):

        assigned_specialization = (
            ideal_specialization
        )

    else:

        assigned_specialization = (
            "General Physician"
        )

    message = generate_message(
        ideal_specialization,
        assigned_specialization
    )

    return {
        "ideal_specialization":
            ideal_specialization,

        "assigned_specialization":
            assigned_specialization,

        "message":
            message
    }