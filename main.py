import asyncio
from aiohttp import ClientSession, ClientError
from datetime import datetime, timedelta
import sys
import json


class PrivatBankAPIClient:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    async def fetch_exchange_rate(self, date: str) -> dict:
        async with ClientSession() as session:
            url = f"{self.BASE_URL}{date}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise Exception(f"HTTP Error: {response.status}")
            except ClientError as e:
                raise Exception(f"Network error: {e}")


class CurrencyFetcher:
    def __init__(self, api_client: PrivatBankAPIClient):
        self.api_client = api_client

    async def get_currency_rates(self, days: int) -> list:
        if not (1 <= days <= 10):
            raise ValueError("Кількість днів повинна бути від 1 до 10.")

        results = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
            data = await self.api_client.fetch_exchange_rate(date)
            rates = self._extract_currency_rates(data, date)
            if rates:
                results.append(rates)
        return results

    @staticmethod
    def _extract_currency_rates(data: dict, date: str) -> dict: 
        if "exchangeRate" not in data:
            return {}

        filtered_data = {
            currency["currency"]: {
                "sale": currency["saleRate"],
                "purchase": currency["purchaseRate"]
            }
            for currency in data["exchangeRate"]
            if currency["currency"] in ["EUR", "USD"]
        }

        return {date: filtered_data} if filtered_data else {}


class ConsoleApp:
    def __init__(self, currency_fetcher: CurrencyFetcher):
        self.currency_fetcher = currency_fetcher

    async def run(self, days: int):
        try:
            rates = await self.currency_fetcher.get_currency_rates(days)
            print(json.dumps(rates, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Помилка: {e}")


async def main():
    if len(sys.argv) != 2:
        print("Використання: py main.py <кількість днів>")
        return

    try:
        days = int(sys.argv[1])
        api_client = PrivatBankAPIClient()
        currency_fetcher = CurrencyFetcher(api_client)
        app = ConsoleApp(currency_fetcher)
        await app.run(days)
    except ValueError:
        print("Помилка: Введіть коректне число днів (1-10).")


if __name__ == "__main__":
    asyncio.run(main())