class CurrencyService:
    def __init__(self):
        self.exchange_rates = {
            "USD": 1.0,
            "EUR": 0.93,
            "JPY": 151.24
        }

    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> dict:
        if from_currency not in self.exchange_rates or to_currency not in self.exchange_rates:
            return {"error": "Unsupported currency"}
        
        usd_amount = amount / self.exchange_rates[from_currency]
        converted = usd_amount * self.exchange_rates[to_currency]
        return {
            "amount": round(converted, 2),
            "currency": to_currency
        }