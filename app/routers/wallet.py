import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.wallet import Wallet, WalletTransaction, TransactionType, WalletTransactionStatus
from app.schemas.wallet import WalletTopupRequest, WalletTopupResponse, WalletBalanceResponse, WalletTransactionResponse
from app.schemas.common import MessageResponse

router = APIRouter()

@router.get("/balance", response_model=WalletBalanceResponse, summary="Get wallet balance")
async def get_balance(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Retrieve the current user's wallet balance and recent transactions."""
    result = await db.execute(
        select(Wallet)
        .where(Wallet.user_id == current_user.id)
    )
    wallet = result.scalar_one_or_none()

    if not wallet:
        # Create wallet if it doesn't exist
        wallet = Wallet(user_id=current_user.id, balance=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        
    transactions_result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(20)
    )
    transactions = transactions_result.scalars().all()

    return WalletBalanceResponse(
        balance=wallet.balance,
        recent_transactions=[
            WalletTransactionResponse.model_validate(t) for t in transactions
        ]
    )

@router.post("/topup", response_model=WalletTopupResponse, summary="Initiate wallet topup")
async def topup_wallet(
    data: WalletTopupRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Initiate a topup using CLICK or PAYME."""
    result = await db.execute(
        select(Wallet).where(Wallet.user_id == current_user.id)
    )
    wallet = result.scalar_one_or_none()
    
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
        
    # Create a pending transaction
    transaction = WalletTransaction(
        wallet_id=wallet.id,
        amount=data.amount,
        transaction_type=TransactionType.DEPOSIT,
        status=WalletTransactionStatus.PENDING,
        payment_method=data.payment_method,
        notes="Topup initiation"
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    # Generate mock payment url
    payment_url = f"https://my.click.uz/services/pay?service_id=123&merchant_id=123&amount={data.amount}&transaction_param={transaction.id}"
    
    return WalletTopupResponse(
        transaction_id=transaction.id,
        amount=transaction.amount,
        payment_url=payment_url
    )

@router.post("/callback/{transaction_id}", response_model=MessageResponse, summary="Simulate payment webhook")
async def payment_callback(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Simulate a successful payment from a provider."""
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.id == transaction_id)
        .options(selectinload(WalletTransaction.wallet))
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if transaction.status == WalletTransactionStatus.COMPLETED:
        return {"message": "Transaction already completed"}
        
    transaction.status = WalletTransactionStatus.COMPLETED
    transaction.notes = "Payment successful via webhook"
    
    # Increment wallet balance
    transaction.wallet.balance += transaction.amount
    
    await db.commit()
    return {"message": "Balance updated successfully"}
