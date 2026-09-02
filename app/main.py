from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from app.database import create_user, get_connection, get_all_tickets, get_helpdesk_user, create_test_helpdesk, create_helpdesk_table, create_user_table, get_ticket_counts, get_dashboard_data, create_ticket_table, get_user, create_test_user
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
from app.auth import secure_hash, verify_password
from pydantic import EmailStr


app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key="secret-key-will-move-to-env"
)


create_user_table()
create_test_user()
create_ticket_table()
create_helpdesk_table()
create_test_helpdesk()
# HTML
templates = Jinja2Templates(directory="./app/templates")

# CSS/ JavaScript
app.mount("/static", StaticFiles(directory="./app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )

@app.post("/login")
async def login(request:Request,
    email: str = Form(...),
    password: str = Form(...)
):
    user = get_user(email)

    if not user:
      return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid email or password."}
    )

    password_hash = user[2]
    if not verify_password(password, password_hash):
        return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": "Invalid email or password."}
        )

    
    request.session["user_id"] = user[0]
    request.session["email"] = user[1]
   
    return RedirectResponse(
        url="/dashboard",
        status_code=303
    )




@app.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )

@app.post("/register")
async def register(
    request: Request,
    email: EmailStr = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)):

    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Passwords do not match."}
        )

    existing_user = get_user(email)

    if (len(password) < 8 
    or not any(char.isdigit() for char in password) 
    or not any(char.isupper() for char in password)
    or not any(char.islower() for char in password)):
        return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "error": "Password must be at least 8 characters and contain an uppercase letter, lowercase letter, and number."
        })

    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "error": "Email already registered."})
    
    password_hash = secure_hash(password)
    created_at = datetime.now().isoformat()

    create_user(email, password_hash,created_at)
    return RedirectResponse(
        url="/",
        status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    if "user_id" not in request.session:
        return RedirectResponse(
            url="/",
            status_code=303)
    email = request.session.get("email")
    user_id = request.session.get("user_id")
    counts, recent_tickets = get_dashboard_data(user_id)
    open_tickets = counts[0]
    in_progress_tickets = counts[1]
    closed_tickets = counts[2]
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "email": email,
            "open_tickets": open_tickets,
            "in_progress_tickets": in_progress_tickets,
            "closed_tickets": closed_tickets,
            "recent_tickets": recent_tickets
        }
    )


@app.get("/tickets", response_class=HTMLResponse)
async def tickets(request: Request):

    if "user_id" not in request.session:
        return RedirectResponse( url="/", status_code=303)
    email = request.session.get("email")

    return templates.TemplateResponse(
        request=request,
        name="ticket.html",
        context={"email": email})

@app.get("/my_tickets", response_class=HTMLResponse)
async def my_tickets(request: Request):

    if "user_id" not in request.session:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    user_id = request.session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            category,
            priority,
            status,
            created_at
        FROM tickets
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))

    tickets = cursor.fetchall()

    cursor.close()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="my_tickets.html",
        context={
            "tickets": tickets
        }
    )


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def view_customer_ticket(request: Request, ticket_id: int):

    if "user_id" not in request.session:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    user_id = request.session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            subject,
            category,
            priority,
            status,
            created_at,
            description,
            response
        FROM tickets
        WHERE id = %s
        AND user_id = %s
    """, (ticket_id, user_id))

    ticket = cursor.fetchone()

    cursor.close()
    conn.close()

    if not ticket:
        return RedirectResponse(
            url="/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="ticket_details.html",
        context={
            "ticket": ticket
        }
    )

@app.post("/tickets/create")
def create_ticket(
    request: Request,
    subject: str = Form(...),
    category: str = Form(...),
    priority: str = Form(...),
    description: str = Form(...)
):
    if "user_id" not in request.session:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    user_id = request.session["user_id"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets (
            user_id,
            subject,
            category,
            priority,
            description
        )
        VALUES (%s, %s, %s, %s, %s)
    """, (
        user_id,
        subject,
        category,
        priority,
        description
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return RedirectResponse(
        url="/tickets",
        status_code=303
    )
   
@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):

    if "user_id" not in request.session:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    email = request.session.get("email")
    user_id = request.session.get("user_id")

    total_tickets, open_tickets, closed_tickets = get_ticket_counts(user_id)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "email": email,
            "user_id": user_id,
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets
        }
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/",
        status_code=303)

@app.get("/helpdesk/login", response_class=HTMLResponse)
async def helpdesk_login_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="admin_login.html"
    )


@app.post("/helpdesk/login")
async def helpdesk_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):

    helpdesk_user = get_helpdesk_user(email)

    if not helpdesk_user:
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Invalid email or password."
            }
        )

    password_hash = helpdesk_user[2]

    if not verify_password(password, password_hash):
        return templates.TemplateResponse(
            request=request,
            name="admin_login.html",
            context={
                "error": "Invalid email or password."
            }
        )

    request.session["helpdesk_id"] = helpdesk_user[0]
    request.session["helpdesk_email"] = helpdesk_user[1]

    return RedirectResponse(
        url="/helpdesk/dashboard",
        status_code=303
    )

@app.get("/helpdesk/dashboard", response_class=HTMLResponse)
async def helpdesk_dashboard(request: Request):

    if "helpdesk_id" not in request.session:
        return RedirectResponse(
            url="/helpdesk/login",
            status_code=303
        )

    tickets = get_all_tickets()

    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={
            "tickets": tickets
        }
    )

@app.get("/helpdesk/ticket/{ticket_id}", response_class=HTMLResponse)
async def helpdesk_ticket(request: Request, ticket_id: int):

    if "helpdesk_id" not in request.session:
        return RedirectResponse(
            url="/helpdesk/login",
            status_code=303
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(""" 
    SELECT 
    tickets.id, 
    tickets.subject, 
    tickets.category, tickets.priority, tickets.status, 
    tickets.created_at, userdata.email, tickets.description, 
    tickets.response 
    FROM tickets 
    JOIN userdata 
        ON tickets.user_id = userdata.id 
    WHERE tickets.id = %s 
    """, 
    (ticket_id,))

    ticket = cursor.fetchone()

    conn.close()

    if not ticket:
        return RedirectResponse(
            url="/helpdesk/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="helpdesk_ticket.html",
        context={
            "ticket": ticket
        }
    )

@app.post("/helpdesk/ticket/{ticket_id}/reply")
async def helpdesk_reply(
    request: Request,
    ticket_id: int,
    reply: str = Form(...)
):

    if "helpdesk_id" not in request.session:
        return RedirectResponse(
            url="/helpdesk/login",
            status_code=303
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tickets
        SET response = %s,
            status = 'In Progress'
        WHERE id = %s
        """,
        (reply, ticket_id)
    )

    conn.commit()
    conn.close()

    return RedirectResponse(
        url=f"/helpdesk/ticket/{ticket_id}",
        status_code=303
    )