const API =
    "https://clinic-booking-chatbot.onrender.com";

function getToken() {
    return localStorage.getItem("token");
}

function requireAuth() {

    const token = getToken();

    if (!token) {
        window.location.href =
            "login.html";
        return false;
    }

    return true;
}

function authHeaders() {

    return {
        "Authorization":
            `Bearer ${getToken()}`
    };
}

function logout() {

    localStorage.removeItem("token");

    window.location.href =
        "login.html";
}


// Pages that require login
const protectedPages = [
    "dashboard.html",
    "appointments.html",
    "doctors.html",
    "patients.html",
    "slots.html"
];

const currentPage =
    window.location.pathname
        .split("/")
        .pop();

if (protectedPages.includes(currentPage)) {
    requireAuth();
}