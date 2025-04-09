# routes/currency_routes.py

from fastapi import APIRouter
from services.currency_service import CurrencyService

router = APIRouter()
currency_service = CurrencyService()


@router.get("/convert")
def convert(amount: float, from_currency: str, to_currency: str):
    return currency_service.convert_currency(amount, from_currency, to_currency)