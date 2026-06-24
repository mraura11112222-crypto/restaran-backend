"""
Analytics router — Boss portal trends, market analysis.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_boss
from app.models.order import Order, OrderItem
from app.models.restaurant import Branch
from app.models.user import User

router = APIRouter()

@router.get("/market-trend", summary="Bozor tendentsiyalari bashorati", dependencies=[Depends(allow_boss)])
async def get_market_trend(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Oylik daromad va buyurtmalar tendensiyasi."""
    try:
        # Get last 12 months data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        result = await db.execute(
            select(
                func.to_char(Order.created_at, 'Mon').label('month'),
                func.sum(Order.total_amount).label('revenue'),
                func.count(Order.id).label('orders')
            )
            .where(Order.created_at >= start_date)
            .group_by(func.to_char(Order.created_at, 'Mon'))
            .order_by(func.min(Order.created_at))
        )
        data = result.fetchall()
        
        months = ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
        trend_data = {month: {'daromad': 0, 'buyurtmalar': 0} for month in months}
        
        for row in data:
            month_name = row.month if row.month in months else 'Yan'
            trend_data[month_name] = {
                'daromad': float(row.revenue or 0),
                'buyurtmalar': row.orders or 0
            }
        
        return {
            "success": True,
            "data": [{"month": k, **v} for k, v in trend_data.items()]
        }
    except Exception as e:
        return {
            "success": False,
            "data": [
                {"month": m, "daromad": 0, "buyurtmalar": 0} for m in ['Yan', 'Fev', 'Mar', 'Apr', 'May', 'Iyun', 'Iyul', 'Avg', 'Sen', 'Okt', 'Noy', 'Dek']
            ]
        }

@router.get("/benchmarking", summary="Filiallararo bench-marketing", dependencies=[Depends(allow_boss)])
async def get_benchmarking(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Filiallar o'rtasida samaradorlik va daromadni solishtirish."""
    try:
        # Get branches with their stats
        result = await db.execute(
            select(
                Branch.name,
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('revenue')
            )
            .outerjoin(Order, Order.branch_id == Branch.id)
            .group_by(Branch.id, Branch.name)
        )
        branches = result.fetchall()
        
        data = []
        for branch in branches:
            data.append({
                "branch": branch.name,
                "order_count": branch.order_count or 0,
                "revenue": float(branch.revenue or 0)
            })
        
        return {
            "success": True,
            "data": data if data else [
                {"branch": "Ma'lumot yo'q", "order_count": 0, "revenue": 0}
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "data": []
        }

@router.get("/kpi", summary="KPI ko'rsatkichlari", dependencies=[Depends(allow_boss)])
async def get_kpi_metrics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user)
):
    """Asosiy KPI ko'rsatkichlari: daromad, buyurtmalar, mijozlar, o'rtacha chek."""
    try:
        # Total revenue
        revenue_result = await db.execute(
            select(func.sum(Order.total_amount)).where(Order.status != 'cancelled')
        )
        total_revenue = revenue_result.scalar() or 0
        
        # Total orders
        orders_result = await db.execute(
            select(func.count(Order.id)).where(Order.status != 'cancelled')
        )
        total_orders = orders_result.scalar() or 0
        
        # Total customers
        customers_result = await db.execute(
            select(func.count(User.id)).where(User.role == 'customer')
        )
        total_customers = customers_result.scalar() or 0
        
        # Average order value
        avg_check = total_revenue / total_orders if total_orders > 0 else 0
        
        return {
            "success": True,
            "data": {
                "revenue": float(total_revenue),
                "orders": total_orders,
                "customers": total_customers,
                "avg_check": float(avg_check)
            }
        }
    except Exception as e:
        return {
            "success": False,
            "data": {
                "revenue": 0,
                "orders": 0,
                "customers": 0,
                "avg_check": 0
            }
        }
