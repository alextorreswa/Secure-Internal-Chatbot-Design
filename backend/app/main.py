from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# ==============================
# Security & Auth Configuration
# ==============================

# In a real Cascade Freight deployment this key would be stored in a secure secret manager
SECRET_KEY = "replace-with-a-long-random-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ==============================
# Fake "database" for prototype
# ==============================

# In the real system this would be PostgreSQL with encrypted storage 
fake_users_db = {
    "alext": {
        "username": "alext",
        "full_name": "Alex Torres",
        "hashed_password": pwd_context.hash("supervisor123"),
        "role": "warehouse_supervisor",
        "disabled": False,
    },
    "jeremyc": {
        "username": "jeremyc",
        "full_name": "Jeremy Clements",
        "hashed_password": pwd_context.hash("compliance123"),
        "role": "compliance_officer",
        "disabled": False,
    },
    "davidd": {
        "username": "davidd",
        "full_name": "David Davis",
        "hashed_password": pwd_context.hash("ceo123"),
        "role": "ceo",
        "disabled": False,
    },
    "ermiyash": {
        "username": "ermiyash",
        "full_name": "Ermiyas Hailemichael",
        "hashed_password": pwd_context.hash("manager123"),
        "role": "warehouse_manager",
        "disabled": False,
    },
}

# Map frontend role values to backend role names
role_map = {
    "supervisor": "warehouse_supervisor",
    "compliance": "compliance_officer",
    "manager": "warehouse_manager",
    "ceo": "ceo",
}

# ==============================
# Pydantic models
# ==============================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    full_name: Optional[str] = None
    role: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


# ==============================
# Auth helper functions
# ==============================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str) -> Optional[UserInDB]:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(db, username: str, password: str) -> Optional[UserInDB]:
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default expiration
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials (invalid or expired token).",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return current_user


# ==============================
# FastAPI app & templates
# ==============================

app = FastAPI(
    title="Secure Internal Chatbot Prototype",
    description=(
        "Proof-of-concept secure login and role-based access for "
        "Cascade Freight Systems' in-house compliance chatbot."
    ),
)

templates = Jinja2Templates(directory="app/templates")

# If you later add CSS/JS, you can serve them from /static
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ==============================
# API endpoints
# ==============================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Redirect to the login page.
    """
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login form.
    """
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...)
):
    """
    Handle login form submission:
    - Validate user credentials
    - Validate selected role against the user's actual role
    - Create JWT token
    - Render the secure chat page
    """
    user = authenticate_user(fake_users_db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    expected_role = role_map.get(role)
    if expected_role != user.role:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid role selection."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    access_message = (
        "You have access to high-level compliance summaries and audit logs."
        if user.role == "compliance_officer"
        else "You can log incidents and view checklists for your assigned warehouse."
    )

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": user,
            "token": access_token,
            "access_message": access_message,
        },
    )


@app.get("/secure-chat", response_class=HTMLResponse)
async def secure_chat_page(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """
    Protected page that simulates a secure internal chatbot.
    """
    if current_user.role == "compliance_officer":
        access_message = "You have access to high-level compliance summaries and audit logs."
    else:
        access_message = "You can log incidents and view checklists for your assigned warehouse."

    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "user": current_user,
            "token": "Use the 'Authorize' button in Swagger; token not shown here.",
            "access_message": access_message,
        },
    )


@app.get("/api/chat")
async def api_chat(
    query: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Prototype chat endpoint (protected).
    For now it just echoes back the query and role.
    Later this will call a local LLM via Ollama.
    """
    response_text = (
        f"[Prototype reply for {current_user.role}] "
        f'You asked: "{query}". In the final system, this would be answered '
        f"using internal compliance documents only."
    )
    return {
        "user": current_user.username,
        "role": current_user.role,
        "answer": response_text,
    }
