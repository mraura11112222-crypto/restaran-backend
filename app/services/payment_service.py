"""
Payment service — payment processing, Click/Payme integration (sandbox).
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException


class PaymentService:
    """Handles payment creation, processing, and reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(
        self,
        order_id: uuid.UUID,
        payment_method: str,
        restaurant_id: uuid.UUID,
    ) -> "Payment":
        """Create a payment record for an order."""
        from app.models.payment import Payment, PaymentMethod, PaymentStatus
        from app.models.order import Order, OrderStatus

        # Get order
        result = await self.db.execute(
            select(Order).where(
                Order.id == order_id,
                Order.restaurant_id == restaurant_id,
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundException("Buyurtma topilmadi")

        # Check if payment already exists
        existing = await self.db.execute(
            select(Payment).where(
                Payment.order_id == order_id,
                Payment.status == PaymentStatus.COMPLETED,
            )
        )
        if existing.scalar_one_or_none():
            raise BadRequestException("Bu buyurtma uchun to'lov allaqachon qilingan")

        method = PaymentMethod(payment_method) if payment_method != "WALLET" else PaymentMethod.CASH

        # Check WALLET balance if WALLET was requested
        if payment_method == "WALLET":
            if not order.customer_id:
                raise BadRequestException("Buyurtmada xaridor ko'rsatilmagan")
            
            from app.models.wallet import Wallet, WalletTransaction, TransactionType, WalletTransactionStatus
            wallet_result = await self.db.execute(select(Wallet).where(Wallet.user_id == order.customer_id))
            wallet = wallet_result.scalar_one_or_none()
            
            if not wallet or wallet.balance < order.total_amount:
                raise BadRequestException("Shaxsiy hisobda mablag' yetarli emas")
                
            # Deduct balance
            wallet.balance -= order.total_amount
            
            # Create Wallet transaction
            w_trans = WalletTransaction(
                id=uuid.uuid4(),
                wallet_id=wallet.id,
                amount=order.total_amount,
                transaction_type=TransactionType.PAYMENT,
                status=WalletTransactionStatus.COMPLETED,
                payment_method="ORDER_PAYMENT",
                notes=f"Order {order.order_number} to'lovi"
            )
            self.db.add(w_trans)

        # For CASH and WALLET — immediately complete
        status = PaymentStatus.COMPLETED if (method == PaymentMethod.CASH or payment_method == "WALLET") else PaymentStatus.PENDING
        transaction_id = None

        if method == PaymentMethod.CASH and payment_method != "WALLET":
            transaction_id = f"CASH-{uuid.uuid4().hex[:8].upper()}"
        elif payment_method == "WALLET":
            transaction_id = f"WALLET-{uuid.uuid4().hex[:8].upper()}"

        payment = Payment(
            id=uuid.uuid4(),
            order_id=order_id,
            amount=order.total_amount,
            payment_method=method,
            status=status,
            transaction_id=transaction_id,
            created_at=datetime.utcnow(),
        )
        self.db.add(payment)

        # If cash or wallet payment, mark order as confirmed
        if status == PaymentStatus.COMPLETED:
            order.status = OrderStatus.CONFIRMED
            order.updated_at = datetime.utcnow()

        await self.db.flush()
        return payment

    async def complete_payment(
        self,
        payment_id: uuid.UUID,
        transaction_id: str,
        provider_data: Optional[dict] = None,
    ) -> "Payment":
        """Complete a pending payment (callback from Click/Payme)."""
        from app.models.payment import Payment, PaymentStatus
        from app.models.order import Order, OrderStatus

        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundException("To'lov topilmadi")

        if payment.status != PaymentStatus.PENDING:
            raise BadRequestException("To'lov allaqachon qayta ishlangan")

        payment.status = PaymentStatus.COMPLETED
        payment.transaction_id = transaction_id
        payment.provider_data = provider_data

        # Update order status
        order_result = await self.db.execute(
            select(Order).where(Order.id == payment.order_id)
        )
        order = order_result.scalar_one_or_none()
        if order:
            order.status = OrderStatus.CONFIRMED
            order.updated_at = datetime.utcnow()

        await self.db.flush()
        return payment

    async def refund_payment(self, payment_id: uuid.UUID) -> "Payment":
        """Refund a completed payment."""
        from app.models.payment import Payment, PaymentStatus

        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        if not payment:
            raise NotFoundException("To'lov topilmadi")

        if payment.status != PaymentStatus.COMPLETED:
            raise BadRequestException("Faqat tugallangan to'lovni qaytarish mumkin")

        payment.status = PaymentStatus.REFUNDED
        await self.db.flush()
        return payment

    async def get_payment_history(
        self,
        restaurant_id: uuid.UUID,
        page: int = 1,
        per_page: int = 20,
        payment_method: Optional[str] = None,
    ) -> dict:
        """Get paginated payment history."""
        from app.models.payment import Payment
        from app.models.order import Order

        query = (
            select(Payment)
            .join(Order, Payment.order_id == Order.id)
            .where(Order.restaurant_id == restaurant_id)
        )

        if payment_method:
            query = query.where(Payment.payment_method == payment_method)

        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        query = query.order_by(Payment.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total, "page": page, "per_page": per_page}

    async def get_daily_report(
        self, restaurant_id: uuid.UUID, report_date: Optional[date] = None
    ) -> dict:
        """Generate daily financial report for cashier/boss."""
        from app.models.payment import Payment, PaymentMethod, PaymentStatus
        from app.models.order import Order, OrderStatus

        target_date = report_date or date.today()

        # Total orders for the day
        orders_q = await self.db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.restaurant_id == restaurant_id,
                cast(Order.created_at, Date) == target_date,
                Order.status != OrderStatus.CANCELLED,
            )
        )
        row = orders_q.one()
        total_orders = row[0] or 0
        total_revenue = row[1] or Decimal("0")

        # Cancelled orders
        cancelled_q = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.restaurant_id == restaurant_id,
                cast(Order.created_at, Date) == target_date,
                Order.status == OrderStatus.CANCELLED,
            )
        )
        cancelled_orders = cancelled_q.scalar() or 0

        # Breakdown by payment method
        breakdown = {}
        for method in PaymentMethod:
            method_q = await self.db.execute(
                select(func.coalesce(func.sum(Payment.amount), 0))
                .join(Order, Payment.order_id == Order.id)
                .where(
                    Order.restaurant_id == restaurant_id,
                    cast(Payment.created_at, Date) == target_date,
                    Payment.payment_method == method,
                    Payment.status == PaymentStatus.COMPLETED,
                )
            )
            breakdown[method.value.lower()] = method_q.scalar() or Decimal("0")

        # Refunded
        refund_q = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .join(Order, Payment.order_id == Order.id)
            .where(
                Order.restaurant_id == restaurant_id,
                cast(Payment.created_at, Date) == target_date,
                Payment.status == PaymentStatus.REFUNDED,
            )
        )
        refunded_amount = refund_q.scalar() or Decimal("0")

        return {
            "date": target_date.isoformat(),
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "cash_amount": float(breakdown.get("cash", 0)),
            "card_amount": float(breakdown.get("card", 0)),
            "click_amount": float(breakdown.get("click", 0)),
            "payme_amount": float(breakdown.get("payme", 0)),
            "cancelled_orders": cancelled_orders,
            "refunded_amount": float(refunded_amount),
        }
