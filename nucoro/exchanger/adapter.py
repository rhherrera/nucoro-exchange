"""Adapter module."""
from datetime import date
import decimal

import requests

from exchanger.exceptions import ProviderUnavailable
from exchanger.models import CurrencyExchangeRate, CurrencyProvider
from nucoro.settings import FIXERIO_APIKEY, FIXERIO_URL


class Adaptee:
    """Generic class for Adaptees."""

    def __init__(self, currency_provider: CurrencyProvider, source_currency: str, exchanged_currency: str, valuation_date: date):
        self.currency_provider = currency_provider
        self.source_currency = source_currency
        self.exchanged_currency = exchanged_currency
        self.valuation_date = valuation_date


class MockAdaptee(Adaptee):
    """Adaptee for Mock Provider."""

    DEFAULT_EUR_BASE_RATES = {'USD': 1.15, 'GBP': 0.80, 'CHF': 1.10, 'EUR': 1}

    def get_mock_exchange_rate(self) -> float:
        """Function that returns a moched exchange rate.

        Returns:
            a mocked exchange rate
        """
        if self.source_currency != self.exchanged_currency:
            last_exchange = CurrencyExchangeRate.objects.filter(source_currency__code=self.source_currency,
                                                                exchanged_currency__code=self.exchanged_currency,
                                                                valuation_date__lte=self.valuation_date)
            last_exchange = last_exchange.order_by('-valuation_date').first()

            if last_exchange:
                return last_exchange.rate_value * decimal.Decimal(1.03)
            else:
                return self.DEFAULT_EUR_BASE_RATES[self.exchanged_currency] / self.DEFAULT_EUR_BASE_RATES[self.source_currency]
        return 1.0


class FixerIoAdaptee(Adaptee):
    """Adaptee for FixerIo Provider."""

    def get_fixier_exchange_rate(self) -> float:
        """Function that returns an exchange rate from fixer_io.

        Returns:
            a fixerio exchange rate

        Raises:
            ProviderUnavailable: the provider is unavailable
        """
        try:
            if self.source_currency != self.exchanged_currency:
                str_date = str(self.valuation_date)
                url = (
                    f'{FIXERIO_URL}/{str_date}?access_key={FIXERIO_APIKEY}'
                    f'&symbols={self.source_currency},{self.exchanged_currency}&format=1'
                )
                response = requests.get(url).json()
                if response['success']:
                    source_rate = response['rates'][self.source_currency]
                    exchanged_rate = response['rates'][self.exchanged_currency]
                    return exchanged_rate / source_rate
                else:
                    raise ProviderUnavailable('No data for that day.')
            return 1.0
        except Exception:
            raise ProviderUnavailable()


class PluginAdaptee(Adaptee):
    """Adaptee for Plugin Provider."""

    def get_custom_exchange_rate(self) -> float:
        """Function that returns an exchange rate from a custom function defined in the admin.

        Returns:
            a custom exchange rate

        Raises:
            ProviderUnavailable: the provider is unavailable
        """
        if self.source_currency != self.exchanged_currency:
            if 'models' not in self.currency_provider.exchange_rate_code:
                exec(f'{self.currency_provider.exchange_rate_code}\nglobal custom_func; custom_func=custom_exchange_rate')
                global custom_func
                return custom_func(self.valuation_date, self.source_currency, self.exchanged_currency)  # type: ignore
            else:
                raise ProviderUnavailable('No data for that day.')
        return 1.0


class Adapter(FixerIoAdaptee, PluginAdaptee, MockAdaptee):
    """Adapter class to unify Adaptees."""

    def __init__(self, currency_provider: CurrencyProvider, source_currency: str, exchanged_currency: str, valuation_date: date):
        self.currency_provider = currency_provider
        self.source_currency = source_currency
        self.exchanged_currency = exchanged_currency
        self.valuation_date = valuation_date

    def get_exchange_rate(self, source_currency: str, exchanged_currency: str, valuation_date: date) -> float:
        """Function that returns an exchange rate from a certain provider.

        Args:
            source_currency: The source currency
            exchanged_currency: The currency in which we want to exchange
            valuation_date: date of the returned rate

        Returns:
            a custom exchange rate
        """
        if self.currency_provider.provider_type == CurrencyProvider.FIXERIO:
            return self.get_fixier_exchange_rate()
        elif self.currency_provider.provider_type == CurrencyProvider.MOCK:
            return self.get_mock_exchange_rate()
        else:
            return self.get_custom_exchange_rate()
