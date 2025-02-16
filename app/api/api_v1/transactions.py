from fastapi import APIRouter, Depends, HTTPException, status
from core.crud.users import get_current_user
from core.models.merch import MerchItem
from core.models.transaction import Transaction
from core.schemas.transfer import SendCoinRequest
from core.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.models.db_helper import db_helper
from core.models.user import User, UserItem

router = APIRouter(
    # prefix=settings.api.v1.transactions,
    tags=["Purchases"]
)

@router.post("/api/sendCoin")
async def send_coin(
    send_request: SendCoinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    # Проверка что пользователь не отправляет сам себе
    if current_user.username == send_request.to_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно отправить монеты самому себе"
        )

    if send_request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Количество монет должно быть положительным"
        )
    
    if current_user.balance < send_request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Недостаточно монет"
        )

    result_rec = await db.execute(
        select(User).where(User.username == send_request.to_user)
    )
    recipient = result_rec.scalars().first()
    
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь-получатель не найден"
        )

    # Дополнительная проверка по ID на случай изменения username
    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невозможно отправить монеты самому себе"
        )

    current_user.balance -= send_request.amount
    recipient.balance += send_request.amount
    
    txn = Transaction(
        sender=current_user.id,
        receiver=recipient.id,
        amount=send_request.amount
    )
    db.add(txn)
    
    await db.commit()
    return {"detail": "Монетки успешно отправлены"}


@router.get("/api/buy/{item}")
async def buy_item(
    item: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(db_helper.session_getter)
):
    try:
        result_merch = await db.execute(select(MerchItem).where(MerchItem.name == item))
        merch = result_merch.scalars().first()

        if not merch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Товар с указанным названием не найден"
            )

        # Проверяем баланс
        if current_user.balance < merch.price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недостаточно монет для покупки товара"
            )
        
        current_user.balance -= merch.price

        user_item = UserItem(name=merch.name, user_id=current_user.id)
        db.add(user_item)
        await db.commit()

        return {"detail": f"Товар '{merch.name}' успешно куплен"}

    except Exception as e:
        await db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при обработке покупки"
        ) from e