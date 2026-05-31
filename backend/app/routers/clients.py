from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.database import get_db
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.middleware.security import get_current_active_user

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("/", response_model=List[ClientResponse])
async def list_clients(
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20, # Paginated by 20 by default
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Search and list clients with pagination. Accessible to all logged-in users.
    Filters on first_name, last_name, tax_id, and email.
    """
    stmt = select(Client).where(Client.is_active == True)

    if search:
        search_filter = f"%{search}%"
        stmt = stmt.where(
            or_(
                Client.first_name.ilike(search_filter),
                Client.last_name.ilike(search_filter),
                Client.tax_id.ilike(search_filter),
                Client.email.ilike(search_filter),
            )
        )

    stmt = stmt.order_by(Client.last_name, Client.first_name).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new client. Checks for unique tax_id.
    """
    if payload.tax_id:
        stmt = select(Client).where(Client.tax_id == payload.tax_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un cliente registrado con ese número de identificación tributaria (DNI/CUIT/CUIL)."
            )

    new_client = Client(**payload.model_dump())
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client_details(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a single client.
    """
    stmt = select(Client).where(Client.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    payload: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update client details.
    """
    stmt = select(Client).where(Client.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    # Check unique tax ID if it's changing
    update_data = payload.model_dump(exclude_unset=True)
    if "tax_id" in update_data and update_data["tax_id"] != client.tax_id:
        stmt_tax = select(Client).where(Client.tax_id == update_data["tax_id"])
        res_tax = await db.execute(stmt_tax)
        if res_tax.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese mismo DNI/CUIT/CUIL."
            )

    for key, value in update_data.items():
        setattr(client, key, value)

    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_200_OK)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Hard-deletes client or soft-deactivates if relationships exist.
    Assistants are blocked from deletes.
    """
    if current_user.role == UserRole.ASSISTANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los asistentes no tienen autorización para eliminar clientes."
        )

    stmt = select(Client).where(Client.id == client_id)
    result = await db.execute(stmt)
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )

    try:
        await db.delete(client)
        await db.commit()
        return {"detail": "Cliente eliminado correctamente"}
    except Exception:
        await db.rollback()
        # Fallback to Soft-Deactivation to protect records
        client.is_active = False
        db.add(client)
        await db.commit()
        return {"detail": "El cliente posee expedientes o actividades. Se procedió a desactivar su ficha de manera segura."}
