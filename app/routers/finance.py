"""
Finance router — Accounting integrations, Tax rules, Currencies.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.permissions import allow_admin
from app.models.finance import FinancialIntegration, TaxRule, Currency

router = APIRouter()


# --- Schemas ---

class CurrencyCreate(BaseModel):
    code: str
    symbol: Optional[str] = None
    exchange_rate: float = 1.0
    is_default: bool = False

class CurrencyResponse(BaseModel):
    id: uuid.UUID
    code: str
    symbol: Optional[str]
    exchange_rate: float
    is_default: bool

    class Config:
        from_attributes = True

class TaxRuleCreate(BaseModel):
    restaurant_id: uuid.UUID
    country_code: str
    tax_name: str
    tax_percentage: float

class FinancialIntegrationCreate(BaseModel):
    restaurant_id: uuid.UUID
    system_name: str  # 1C, QUICKBOOKS
    api_credentials: Optional[dict] = None


# --- Currency Endpoints ---

@router.get("/transactions", summary="Barcha tranzaksiyalar")
async def list_transactions(db: AsyncSession = Depends(get_db)):
    return [
        { "id": "1", "date": "2025-01-15", "description": "Asosiy tushumlar", "amount": 12500000, "type": "income", "category": "Sotuv" },
        { "id": "2", "description": "Oziq-ovqat mahsulotlari", "amount": -4500000, "type": "expense", "category": "Ta'minot" },
        { "id": "3", "description": "Soliq to'lovlari", "amount": -1200000, "type": "expense", "category": "Soliq" },
        { "id": "4", "description": "Filial tushumi", "amount": 8400000, "type": "income", "category": "Sotuv" },
    ]

@router.get("/currencies", summary="Barcha valyutalar")
async def list_currencies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Currency))
    return result.scalars().all()


@router.post("/currencies", summary="Valyuta qo'shish", dependencies=[Depends(allow_admin)])
async def create_currency(
    body: CurrencyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    currency = Currency(
        code=body.code.upper(),
        symbol=body.symbol,
        exchange_rate=body.exchange_rate,
        is_default=body.is_default,
    )
    db.add(currency)
    await db.commit()
    await db.refresh(currency)
    return currency


@router.put("/currencies/{currency_id}/rate", summary="Kursni yangilash", dependencies=[Depends(allow_admin)])
async def update_exchange_rate(
    currency_id: uuid.UUID,
    new_rate: float,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(select(Currency).where(Currency.id == currency_id))
    currency = result.scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=404, detail="Valyuta topilmadi")
    currency.exchange_rate = new_rate
    await db.commit()
    return {"detail": f"{currency.code} kursi {new_rate} ga yangilandi"}


# --- Tax Rules Endpoints ---

@router.get("/tax-rules/{restaurant_id}", summary="Soliq qoidalari", dependencies=[Depends(allow_admin)])
async def list_tax_rules(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(TaxRule).where(TaxRule.restaurant_id == restaurant_id, TaxRule.is_active == True)
    )
    return result.scalars().all()


@router.post("/tax-rules", summary="Soliq qoidasi yaratish", dependencies=[Depends(allow_admin)])
async def create_tax_rule(
    body: TaxRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    rule = TaxRule(
        restaurant_id=body.restaurant_id,
        country_code=body.country_code.upper(),
        tax_name=body.tax_name,
        tax_percentage=body.tax_percentage,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


# --- Financial Integration Endpoints ---

@router.get("/integrations/{restaurant_id}", summary="Buxgalteriya integratsiyasi", dependencies=[Depends(allow_admin)])
async def get_financial_integration(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    result = await db.execute(
        select(FinancialIntegration).where(FinancialIntegration.restaurant_id == restaurant_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="Integratsiya topilmadi")
    return integration


@router.post("/integrations", summary="Buxgalteriya integratsiyasini sozlash", dependencies=[Depends(allow_admin)])
async def setup_financial_integration(
    body: FinancialIntegrationCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    integration = FinancialIntegration(
        restaurant_id=body.restaurant_id,
        system_name=body.system_name.upper(),
        api_credentials=body.api_credentials,
    )
    db.add(integration)
    await db.commit()
    await db.refresh(integration)
    return integration
