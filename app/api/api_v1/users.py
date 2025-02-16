from fastapi import APIRouter, Depends, HTTPException, status
from core.auth.token import create_access_token
from core.crud.users import get_current_user
from core.models.transaction import Transaction
from core.schemas.auth import AuthRequest, AuthResponse
from core.schemas.base_response import InfoResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from collections import Counter
import bcrypt

from core.models.db_helper import db_helper
from core.models.user import User, UserItem


router = APIRouter(
    # prefix=settings.api.v1.users,
    tags=["Users"]
)


@router.post("/api/auth", response_model=AuthResponse)
async def auth(
    auth_request: AuthRequest, 
    db: AsyncSession = Depends(db_helper.session_getter)
):
    username = auth_request.username.strip()
    password = auth_request.password.strip()
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Имя пользователя и пароль обязательны"
        )
    
    password_bytes = password.encode('utf-8')
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if user:
        try:
            if not bcrypt.checkpw(password_bytes, user.password.encode('utf-8')):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный пароль"
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка проверки пароля: {str(e)}"
            )
    else:
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        
        user = User(
            username=username,
            password=hashed.decode('utf-8'),
            balance=100
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token(username=user.username)
    return {"access_token": access_token}


@router.get(
    "/api/info",
    response_model=InfoResponse,
    responses={
        status.HTTP_200_OK: {"description": "Успешный ответ."},
        status.HTTP_400_BAD_REQUEST: {"description": "Неверный запрос."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Неавторизован."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Внутренняя ошибка сервера."},
    }
)
async def get_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
) -> InfoResponse:
    try:
        coin_balance = current_user.balance

        result_ui = await db.execute(
            select(UserItem).where(UserItem.user_id == current_user.id))
        user_items = result_ui.scalars().all()

        inventory_list = [item.name for item in user_items]

        inventory_counts = Counter(inventory_list)
        inventory = [{"type": item, "quantity": count} 
                    for item, count in inventory_counts.items()]
        incoming_txns = (await db.execute(
            select(Transaction).where(Transaction.receiver == current_user.id)
        )).scalars().all()
        
        outgoing_txns = (await db.execute(
            select(Transaction).where(Transaction.sender == current_user.id)
        )).scalars().all()

        async def get_username(user_id: int) -> str:
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalars().first()
            return user.username if user else "Неизвестный пользователь"

        transactions_in = []
        for txn in incoming_txns:
            transactions_in.append({
                "counterparty": await get_username(txn.sender),
                "total_amount": int(txn.amount)
            })

        transactions_out = []
        for txn in outgoing_txns:
            transactions_out.append({
                "counterparty": await get_username(txn.receiver),
                "total_amount": int(txn.amount)
            })

        return InfoResponse(
            coin_balance=coin_balance,
            inventory=inventory,
            transactions_in=transactions_in,
            transactions_out=transactions_out
        )
    
    except Exception as e:
        print(f"Ошибка: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"errors": "Внутренняя ошибка сервера."}
        ) from e