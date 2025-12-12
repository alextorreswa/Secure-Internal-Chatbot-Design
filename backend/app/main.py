from datetime import datetime, timedelta
from typing import Optional, List
import os

import requests
from fastapi import (
    FastAPI,
    Depends,
    Request,
    Form,
    status,
    HTTPException
)
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from jose import jwt, JWTError
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# Basic security config (prototype only – hard-coded key)
# -----------------------------------------------------------------------------
SECRET_KEY = "super-secret-demo-key-for-cascade-freight-only"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# -----------------------------------------------------------------------------
# Ollama / AI model configuration
# -----------------------------------------------------------------------------
# Toggle AI integration on/off via env var:
#   set OLLAMA_ENABLED=true
#   set OLLAMA_MODEL=mistral
#   set OLLAMA_API_URL=http://localhost:11434/api/chat
OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "false").lower() == "true"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/api/chat")


# -----------------------------------------------------------------------------
# Demo "database" – users, roles, plus fake shipments/policies
# -----------------------------------------------------------------------------

RAW_USERS = {
    "alext": {
        "full_name": "Alex Torres",
        "role": "dispatcher",  # Dispatcher role
        "password": "supervisor123",
    },
    "jeremyc": {
        "full_name": "Jeremy Clements",
        "role": "compliance_officer",
        "password": "compliance123",
    },
    "ermiyash": {
        "full_name": "Ermiyas Hailemichael",
        "role": "warehouse_manager",
        "password": "manager123",
    },
    "davidd": {
        "full_name": "David Davis",
        "role": "admin",  # Treat CEO as admin for demo
        "password": "ceo123",
    },
}

# Copy into a "DB" structure we’ll use everywhere else
USERS_DB = {}
for username, data in RAW_USERS.items():
    USERS_DB[username] = {
        "username": username,
        "full_name": data["full_name"],
        "role": data["role"],
        "password": data["password"],  # plain text for demo
    }


def authenticate_user(username: str, password: str):
    """
    Simple prototype authentication:
    - Look up user
    - Compare plain-text password
    """
    user = USERS_DB.get(username)
    if not user:
        return None
    if password != user["password"]:
        return None
    return user


# Fake shipment & policy data just for chatbot responses
SHIPMENTS = {
    "CFS-1001": {
        "status": "In transit",
        "eta": "Today 4:30 PM",
        "driver": "Driver-07",
        "route": "Seattle → Spokane",
        "exceptions": [],
    },
    "CFS-1002": {
        "status": "Delayed",
        "eta": "Tomorrow 9:00 AM",
        "driver": "Driver-04",
        "route": "Everett → Portland",
        "exceptions": ["Weather delay on I-5"],
    },
    "CFS-1003": {
        "status": "Delivered",
        "eta": "Delivered 08:15 AM",
        "driver": "Driver-02",
        "route": "Kent → Yakima",
        "exceptions": [],
    },
}

POLICIES = {
    "hazmat": (
        "Hazmat Safety Policy: Drivers must complete annual hazmat training, "
        "carry updated SDS sheets, and perform a 360° walk-around inspection "
        "before departure. Any leak or odor must be reported immediately to dispatch."
    ),
    "ppe": (
        "PPE Policy: High-visibility vest, safety shoes, and gloves are required "
        "in all warehouse zones. Hearing protection is required in loading bays 2–5."
    ),
    "hours_of_service": (
        "Hours-of-Service Policy: Maximum 11 hours driving after 10 consecutive "
        "hours off duty. Dispatch must be notified before any potential violation."
    ),
}

CONTACTS = {
    "dispatch": "Dispatch Desk: dispatch@cascadefreight.local · ext. 221",
    "hr": "HR: hr@cascadefreight.local · ext. 205",
    "it": "IT Helpdesk: it-help@cascadefreight.local · ext. 250",
}

# In-memory chat log for audit demo
CHAT_LOG: List[dict] = []


# -----------------------------------------------------------------------------
# Pydantic models
# -----------------------------------------------------------------------------
class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    topic: str
    role: str
    timestamp: str


# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_from_request(request: Request) -> dict:
    """
    Reads JWT from cookie 'access_token'. If invalid or missing, raises 401.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = USERS_DB.get(token_data.username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# -----------------------------------------------------------------------------
# FastAPI app & templates
# -----------------------------------------------------------------------------
app = FastAPI(title="Cascade Freight Secure Chatbot – Prototype")

templates = Jinja2Templates(directory="app/templates")

# (Optional) Mount /static if you later add CSS/JS files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# -----------------------------------------------------------------------------
# Routes – login & basic nav
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    # Simple redirect to login page
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid username or password. Please try again.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # Create token with embedded username + role
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    response = RedirectResponse(url="/chat", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,  # For local demo only – set True + HTTPS in production
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, current_user: dict = Depends(get_current_user_from_request)):
    """
    Protected page that shows the chatbot UI.
    """
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "username": current_user["username"],
            "full_name": current_user["full_name"],
            "role": current_user["role"],
        },
    )


# -----------------------------------------------------------------------------
# Chatbot logic – topic detection + rule-based fallbacks
# -----------------------------------------------------------------------------
def detect_topic(message: str) -> str:
    msg = message.lower()

    if any(x in msg for x in ["shipment", "track", "eta", "delivery", "#cfs-"]):
        return "shipment_tracking"
    if any(x in msg for x in ["driver", "assignment", "dispatch"]):
        return "dispatch_coordination"
    if any(x in msg for x in ["policy", "vacation", "sick leave", "safety", "hazmat", "ppe"]):
        return "employee_support"
    if any(x in msg for x in ["audit", "log", "compliance", "checklist"]):
        return "compliance_audit"
    if any(x in msg for x in ["contact", "hr", "it", "helpdesk", "phone", "email"]):
        return "contact_directory"

    return "general"


def handle_shipment_query(message: str, role: str) -> str:
    msg = message.upper()

    # Look for a shipment ID like CFS-1001
    shipment_id = None
    for sid in SHIPMENTS.keys():
        if sid in msg:
            shipment_id = sid
            break

    if not shipment_id:
        return (
            "Please specify a shipment ID, for example: "
            "\"Track shipment CFS-1001\"."
        )

    shipment = SHIPMENTS[shipment_id]
    base_info = (
        f"Shipment {shipment_id}\n"
        f" • Status: {shipment['status']}\n"
        f" • ETA: {shipment['eta']}\n"
        f" • Route: {shipment['route']}"
    )

    exceptions_info = ""
    if shipment["exceptions"]:
        exceptions_info = (
            "\n • Exception alerts: "
            + "; ".join(shipment["exceptions"])
        )

    # Role-based flavor
    if role == "dispatcher":
        return (
            base_info
            + f"\n • Current driver: {shipment['driver']}"
            + exceptions_info
            + "\n\nAll details are logged for audit purposes."
        )
    elif role in ("warehouse_manager", "admin"):
        return (
            base_info
            + f"\n • Current driver: {shipment['driver']}"
            + exceptions_info
            + "\n\nYou can use the internal TMS to reassign this shipment if needed."
        )
    elif role == "driver":
        return (
            base_info
            + "\n\nAs a driver, you can only view your own assigned shipments. "
              "Contact dispatch if something looks incorrect."
        )
    else:
        return (
            base_info
            + "\n\nYour role has read-only access to high-level shipment status."
        )


def handle_dispatch_query(message: str, role: str) -> str:
    if role != "dispatcher" and role not in ("warehouse_manager", "admin"):
        return (
            "Dispatch coordination features are restricted. "
            "Only Dispatch and Management can reassign drivers or shipments."
        )

    return (
        "Dispatch coordination prototype:\n"
        " • You can ask things like: \"Which driver has shipment CFS-1002?\"\n"
        " • In the full system, this would write an assignment change to the "
        "audit log and update the TMS.\n\n"
        "For now, use shipment tracking, policy queries, and contact lookup "
        "to see end-to-end chatbot behavior."
    )


def handle_policy_query(message: str) -> str:
    msg = message.lower()
    if "hazmat" in msg:
        return POLICIES["hazmat"]
    if "ppe" in msg or "safety gear" in msg:
        return POLICIES["ppe"]
    if "hours" in msg or "hos" in msg or "service" in msg:
        return POLICIES["hours_of_service"]

    return (
        "I can help with these policies right now:\n"
        " • Hazmat safety\n"
        " • PPE requirements\n"
        " • Hours-of-service rules\n\n"
        "Try asking \"What is our hazmat safety policy?\""
    )


def handle_contact_query(message: str) -> str:
    msg = message.lower()
    if "dispatch" in msg:
        return CONTACTS["dispatch"]
    if "hr" in msg:
        return CONTACTS["hr"]
    if "it" in msg or "helpdesk" in msg:
        return CONTACTS["it"]

    return (
        "Here are some internal contacts:\n"
        f" • {CONTACTS['dispatch']}\n"
        f" • {CONTACTS['hr']}\n"
        f" • {CONTACTS['it']}\n"
        "You can ask for a specific department, for example "
        "\"Contact HR\" or \"IT helpdesk phone\"."
    )


def handle_compliance_query(role: str) -> str:
    if role not in ("compliance_officer", "admin"):
        return (
            "Compliance and audit checklists are restricted to "
            "Compliance Officers and Admins.\n\n"
            "If you believe you need access, please contact your supervisor."
        )

    return (
        "Compliance & Audit prototype:\n"
        " • I can summarize what an internal audit checklist might cover.\n"
        " • In production, each completed checklist would be logged with "
        "timestamp, user, and findings.\n\n"
        "Example checklist items:\n"
        "  1. Verify that all hazmat shipments have signed manifests.\n"
        "  2. Confirm that driver HOS logs are complete for the audit period.\n"
        "  3. Review random sample of delivery PODs for required signatures."
    )


def handle_general_query(message: str, role: str) -> str:
    return (
        "I’m Cascade Freight’s internal assistant prototype. "
        "Right now I can help you with:\n"
        " • Tracking shipments (e.g., \"Track shipment CFS-1001\")\n"
        " • Asking about safety or HR policies "
        "(e.g., \"What is the hazmat safety policy?\")\n"
        " • Looking up internal contacts (e.g., \"Contact HR\")\n"
        " • Compliance checklist guidance (for Compliance / Admin roles)\n\n"
        f"Your current role is: {role or 'unknown'}."
    )


# -----------------------------------------------------------------------------
# AI integration helpers – build prompt and call Ollama
# -----------------------------------------------------------------------------
def build_ai_prompt(message: str, user: dict, topic: str) -> str:
    """
    Build a prompt that gives the LLM context about:
    - Company
    - User role
    - Available data (shipments, policies, contacts)
    """
    role = user["role"]
    username = user["username"]

    base_context = (
        "You are an internal assistant for Cascade Freight Systems, "
        "a regional logistics and trucking company. You must ALWAYS respect "
        "role-based access and never invent shipment IDs or policies.\n\n"
        f"Current user: {username}\n"
        f"User role: {role}\n"
        f"Detected topic: {topic}\n\n"
        "Available shipment data:\n"
    )

    # Add shipments
    for sid, info in SHIPMENTS.items():
        base_context += (
            f" - {sid}: status={info['status']}, eta={info['eta']}, "
            f"driver={info['driver']}, route={info['route']}, "
            f"exceptions={'; '.join(info['exceptions']) if info['exceptions'] else 'none'}\n"
        )

    base_context += "\nPolicies:\n"
    base_context += f" - hazmat: {POLICIES['hazmat']}\n"
    base_context += f" - ppe: {POLICIES['ppe']}\n"
    base_context += f" - hours_of_service: {POLICIES['hours_of_service']}\n"

    base_context += "\nContacts:\n"
    base_context += f" - dispatch: {CONTACTS['dispatch']}\n"
    base_context += f" - hr: {CONTACTS['hr']}\n"
    base_context += f" - it: {CONTACTS['it']}\n"

    instructions = (
        "\nGuidelines for your answer:\n"
        " - Answer using the data above when possible.\n"
        " - If the user asks for a shipment ID that is not listed, say "
        "\"I don't have data for that shipment ID in this prototype.\"\n"
        " - If the user is not allowed to see something based on role, explain "
        "that access is restricted.\n"
        " - Keep the answer concise and practical.\n"
    )

    return (
        base_context
        + instructions
        + "\n\nUser question:\n"
        + message
    )


def generate_ai_reply(message: str, user: dict, topic: str) -> str:
    """
    Call Ollama's chat API to generate an answer.
    Falls back to raising an exception if something goes wrong.
    """
    if not OLLAMA_ENABLED:
        raise RuntimeError("Ollama integration disabled")

    prompt = build_ai_prompt(message, user, topic)

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are CascadeBot, an internal assistant for Cascade Freight Systems. "
                    "You must be accurate, concise, and never fabricate unknown internal data."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
    }

    response = requests.post(
        OLLAMA_API_URL,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    # Ollama /api/chat returns {"message": {"role": "assistant", "content": "..."}}
    message_obj = data.get("message") or {}
    content = message_obj.get("content")

    if not content:
        raise RuntimeError("Empty response from Ollama")

    return content.strip()


# -----------------------------------------------------------------------------
# /api/chat – main chatbot endpoint
# -----------------------------------------------------------------------------
@app.post("/api/chat", response_model=ChatResponse)
async def chat_api(
    request: Request,
    payload: ChatRequest,
    current_user: dict = Depends(get_current_user_from_request),
):
    user_role = current_user["role"]
    message = payload.message.strip()

    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    topic = detect_topic(message)

    # First: try AI model (if enabled). If it fails, fall back to rule-based logic.
    ai_reply: Optional[str] = None
    if OLLAMA_ENABLED:
        try:
            ai_reply = generate_ai_reply(message, current_user, topic)
        except Exception as exc:
            # For demo: log to console and continue with fallback
            print(f"[WARN] Ollama call failed: {exc}")

    if ai_reply is not None:
        reply = ai_reply
    else:
        # Fallback/rule-based engine (what you already had)
        if topic == "shipment_tracking":
            reply = handle_shipment_query(message, user_role)
        elif topic == "dispatch_coordination":
            reply = handle_dispatch_query(message, user_role)
        elif topic == "employee_support":
            reply = handle_policy_query(message)
        elif topic == "contact_directory":
            reply = handle_contact_query(message)
        elif topic == "compliance_audit":
            reply = handle_compliance_query(user_role)
        else:
            reply = handle_general_query(message, user_role)

    timestamp = datetime.utcnow().isoformat()

    # Simple in-memory audit log
    CHAT_LOG.append(
        {
            "timestamp": timestamp,
            "username": current_user["username"],
            "role": user_role,
            "message": message,
            "reply": reply,
            "topic": topic,
            "used_ai": ai_reply is not None,
        }
    )

    return ChatResponse(
        reply=reply,
        topic=topic,
        role=user_role,
        timestamp=timestamp,
    )


# -----------------------------------------------------------------------------
# Optional: simple admin view of recent logs (for demo)
# -----------------------------------------------------------------------------
@app.get("/admin/logs")
async def view_logs(current_user: dict = Depends(get_current_user_from_request)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    latest = CHAT_LOG[-25:]
    return JSONResponse(content={"count": len(latest), "entries": latest})
