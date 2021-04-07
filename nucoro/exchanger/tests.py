"""Test module."""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from unittest.mock import patch

from django.test import TestCase  # type: ignore

from exchanger.interactors import _get_exchange_rate, currency_converter, get_exchange_rates, time_weight_rate
from exchanger.models import Currency, CurrencyExchangeRate, CurrencyProvider


class MockFixerIOResponseSuccess:
    """Mock for FixerIo."""
    def __init__(self):
        self.status_code = 200

    def json(self) -> dict:
        """Returns the mock json response.

        Returns:
            a dict that represent the fixerio answer.
        """
        date_fixerio = str(datetime.today().date() - timedelta(days=10))
        return {
            "success": True,
            "timestamp": 1617494399,
            "historical": True,
            "base": "EUR",
            "date": date_fixerio,
            "rates": {
                "EUR": 1,
                "CHF": 1.108513,
                "USD": 1.17593,
                "GBP": 0.850275
            }
        }


class MockFixerIOResponseFail:
    """Mock for FixerIo Fail."""
    def __init__(self):
        self.status_code = 200

    def json(self) -> dict:
        """Returns the mock json response.

        Returns:
            a dict that represent the fixerio answer.
        """
        date_fixerio = str(datetime.today().date() - timedelta(days=12))
        return {
            "success": False,
            "timestamp": 1617494399,
            "historical": True,
            "base": "EUR",
            "date": date_fixerio
        }


class ExchangeTestCase(TestCase):
    """Exchange rate test case."""
    def setUp(self) -> None:
        """Setup function for ExchangeTestCase."""
        self.today = datetime.today().date()
        self.yesterday = (datetime.today() - timedelta(days=1)).date()
        self.source = Currency.objects.get(code="EUR")
        self.usd = Currency.objects.get(code="USD")
        self.gbp = Currency.objects.get(code="GBP")
        self.chf = Currency.objects.get(code="CHF")
        self.currency_codes = [self.source.code, self.usd.code, self.gbp.code, self.chf.code]
        self.exchanges = {
            self.usd.code: {'data': [(self.yesterday, Decimal(1.12)), (self.today, Decimal(1.15))], 'object': self.usd},
            self.gbp.code: {'data': [(self.yesterday, Decimal(0.85)), (self.today, Decimal(0.80))], 'object': self.gbp},
            self.chf.code: {'data': [(self.yesterday, Decimal(1.05)), (self.today, Decimal(1.08))], 'object': self.chf},
            self.source.code: {'data': [(self.yesterday, Decimal(1)), (self.today, Decimal(1))], 'object': self.source}
        }
        self.currency_exchange_rates = []
        for exchange in self.exchanges.values():
            for data_row in exchange['data']:
                self.currency_exchange_rates.append(
                    CurrencyExchangeRate.objects.create(
                        source_currency=self.source, exchanged_currency=exchange['object'],
                        valuation_date=data_row[0], rate_value=data_row[1])
                )

    def test_exchange_rates(self) -> None:
        """Test get_exchange_rates interactor."""
        data = get_exchange_rates('EUR', self.yesterday, self.today)

        for rate_date, value in data.items():
            for code, rate in value.items():
                for data_tuple in self.exchanges[code]['data']:
                    if str(data_tuple[0]) == rate_date:
                        expected_rate = float(data_tuple[1])
                        self.assertEqual(float(rate), expected_rate)

    def test_currency_converter(self) -> None:
        """Test currency_converter interactor."""
        data = currency_converter('EUR', 'USD', Decimal(10))

        expected_response = {
            'source_currency': 'EUR',
            'exchanged_currency': 'USD',
            'amount_in_EUR': Decimal(10),
            'rate_value': Decimal(1.15),
            'amount_after_exchange': Decimal(10) * Decimal(1.15)
        }
        for key, value in data.items():
            if key in ['source_currency', 'exchanged_currency']:
                self.assertEqual(value, expected_response[key])
            else:
                self.assertEqual(float(value), float(expected_response[key]))  # type: ignore

    def test_time_weight_rate(self) -> None:
        """Test time_weight_rate interactor."""
        CurrencyProvider.objects.update()
        data = time_weight_rate('EUR', 'USD', Decimal(100), self.yesterday)
        final_amount_in_EUR = Decimal(100) * Decimal(1.12) / Decimal(1.15)

        expected_response = {
            'initial_amount_in_EUR': Decimal(100),
            'final_amount_in_EUR': final_amount_in_EUR,
            'amount_in_USD': Decimal(100) * Decimal(1.12),
            'initial_exchange_rate': Decimal(1.12),
            'current_exchange_rate': Decimal(1.15),
            'twr_percentage': ((final_amount_in_EUR - Decimal(100)) / Decimal(100)) * 100
        }
        for key, value in data.items():
            self.assertEqual(round(float(value), 6), round(float(expected_response[key]), 6))

    @patch("requests.get", return_value=MockFixerIOResponseSuccess())
    def test_provider_fixerIo(self, mocked: Any) -> None:
        """Test fixerIo provider.

        Args:
            mocked: the mock of the call to fixerIo.
        """
        ten_days_ago_date = self.today - timedelta(days=10)
        data = _get_exchange_rate('EUR', 'USD', ten_days_ago_date)

        self.assertEqual(data.source_currency, self.source)  # type: ignore
        self.assertEqual(data.exchanged_currency, self.usd)  # type: ignore
        self.assertEqual(data.valuation_date, ten_days_ago_date)  # type: ignore
        self.assertEqual(float(data.rate_value), 1.17593)  # type: ignore

    @patch("requests.get", return_value=MockFixerIOResponseFail())
    def test_provider_mock(self, mocked: Any) -> None:
        """Test mock provier, after fixerIo fails.

        Args:
            mocked: the mock of the call to fixerIo.
        """
        twelve_days_ago_date = self.today - timedelta(days=12)
        data = _get_exchange_rate('EUR', 'USD', twelve_days_ago_date)

        self.assertEqual(data.source_currency, self.source)  # type: ignore
        self.assertEqual(data.exchanged_currency, self.usd)  # type: ignore
        self.assertEqual(data.valuation_date, twelve_days_ago_date)  # type: ignore
        self.assertEqual(float(data.rate_value), 1.15)  # type: ignore
