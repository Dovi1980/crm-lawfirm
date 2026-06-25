import structlog
from datetime import datetime, date
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.client import Client
from app.models.case import Case, CaseStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.interaction import Interaction
from app.middleware.security import get_current_active_user
from app.routers.auth import router as auth_router, limiter
from app.routers.users import router as users_router
from app.routers.clients import router as clients_router
from app.routers.cases import router as cases_router
from app.routers.interactions import router as interactions_router
from app.routers.tasks import router as tasks_router
from app.routers.ai import router as ai_router
from app.routers.documents import router as documents_router
from app.routers.templates import router as templates_router

# Configure Structured Logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Configure SlowAPI Rate Limiter State
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Sub-Routers under '/api' prefix
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(clients_router, prefix=settings.API_V1_STR)
app.include_router(cases_router, prefix=settings.API_V1_STR)
app.include_router(interactions_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(templates_router, prefix=settings.API_V1_STR)


@app.get("/api/health")
async def health_check():
    """System health validation endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.get("/api/dashboard/stats")
async def get_dashboard_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Computes real-time KPI metrics and activity lists for the primary dashboard.
    Supports Lawyer data isolation:
    - Lawyers only count their own tasks/cases/activities.
    - Admins and Assistants view whole-studio stats.
    """
    today = date.today()
    start_of_month = date(today.year, today.month, 1)

    # 1. Total Active Clients (Visible to all)
    stmt_clients = select(func.count(Client.id)).where(Client.is_active == True)
    res_clients = await db.execute(stmt_clients)
    total_clients = res_clients.scalar() or 0

    # 2. Scoped Case Queries
    stmt_open_cases = select(func.count(Case.id)).where(
        and_(
            Case.status != CaseStatus.CERRADO,
            Case.status != CaseStatus.ARCHIVADO
        )
    )
    stmt_closed_this_month = select(func.count(Case.id)).where(
        and_(
            Case.status == CaseStatus.CERRADO,
            Case.start_date >= start_of_month # Proxy for close date in MVP
        )
    )

    if current_user.role == UserRole.LAWYER:
        stmt_open_cases = stmt_open_cases.where(Case.assigned_lawyer_id == current_user.id)
        stmt_closed_this_month = stmt_closed_this_month.where(Case.assigned_lawyer_id == current_user.id)

    res_open = await db.execute(stmt_open_cases)
    total_open_cases = res_open.scalar() or 0

    res_closed = await db.execute(stmt_closed_this_month)
    total_closed_cases_month = res_closed.scalar() or 0

    # 3. Scoped Task Queries
    # Pending tasks of the current user
    stmt_pending_tasks = select(func.count(Task.id)).where(
        and_(
            Task.assigned_to_id == current_user.id,
            or_(
                Task.status == TaskStatus.PENDIENTE,
                Task.status == TaskStatus.EN_PROGRESO
            )
        )
    )
    res_pending = await db.execute(stmt_pending_tasks)
    pending_tasks_user = res_pending.scalar() or 0

    # Overdue tasks (due_date < today AND not complete/cancelled)
    stmt_overdue_tasks = select(func.count(Task.id)).where(
        and_(
            Task.due_date < today,
            Task.status != TaskStatus.COMPLETADA,
            Task.status != TaskStatus.CANCELADA
        )
    )
    if current_user.role == UserRole.LAWYER:
        stmt_overdue_tasks = stmt_overdue_tasks.where(Task.assigned_to_id == current_user.id)

    res_overdue = await db.execute(stmt_overdue_tasks)
    overdue_tasks = res_overdue.scalar() or 0

    # 4. Recent Activity Stream (Latest 10 Interactions)
    stmt_activities = select(Interaction).order_by(Interaction.interaction_date.desc()).limit(10)
    
    if current_user.role == UserRole.LAWYER:
        # Filter activities relating to the lawyer's cases or registered by them
        stmt_lawyer_cases = select(Case.id).where(Case.assigned_lawyer_id == current_user.id)
        cases_ids_res = await db.execute(stmt_lawyer_cases)
        cases_ids = cases_ids_res.scalars().all()
        stmt_activities = stmt_activities.where(
            or_(
                Interaction.case_id.in_(cases_ids),
                Interaction.user_id == current_user.id
            )
        )

    res_activities = await db.execute(stmt_activities)
    activities = res_activities.scalars().all()

    # Serialize activities to list
    recent_activities = []
    for act in activities:
        # Load registered by email
        stmt_user = select(User.first_name, User.last_name).where(User.id == act.user_id)
        res_user = await db.execute(stmt_user)
        user_info = res_user.first()
        user_name = f"{user_info[0]} {user_info[1]}" if user_info else "Sistema"
        
        recent_activities.append({
            "id": act.id,
            "type": act.interaction_type.value,
            "description": act.description,
            "date": act.interaction_date.isoformat(),
            "duration": act.duration_minutes,
            "author": user_name
        })

    # 5. Urgent Tasks (Priority = URGENTE AND pending/in_progress, max 5)
    stmt_urgents = select(Task).where(
        and_(
            Task.priority == TaskPriority.URGENTE,
            or_(
                Task.status == TaskStatus.PENDIENTE,
                Task.status == TaskStatus.EN_PROGRESO
            )
        )
    ).order_by(Task.due_date.asc()).limit(5)

    if current_user.role == UserRole.LAWYER:
        stmt_urgents = stmt_urgents.where(Task.assigned_to_id == current_user.id)

    res_urgents = await db.execute(stmt_urgents)
    urgents = res_urgents.scalars().all()
    urgent_tasks = []
    for task in urgents:
        urgent_tasks.append({
            "id": task.id,
            "title": task.title,
            "due_date": task.due_date.isoformat(),
            "status": task.status.value
        })

    return {
        "kpis": {
            "total_clients": total_clients,
            "total_open_cases": total_open_cases,
            "total_closed_cases_month": total_closed_cases_month,
            "pending_tasks_user": pending_tasks_user,
            "overdue_tasks": overdue_tasks
        },
        "recent_activities": recent_activities,
        "urgent_tasks": urgent_tasks
    }
