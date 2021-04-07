"""Interactors module."""
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

import django_rq  # type: ignore

from exchanger.adapter import Adapter
from exchanger.exceptions import ProviderUnavailable
from exchanger.models import Currency, CurrencyExchangeRate, CurrencyProvider


def get_exchange_rates(source_currency: str, date_from: date, date_to: date) -> dict:
    """Retrieve the exchange rates in all accepted currencies.

    Args:
        source_currency: The source currency to get rates
        date_from: from which date retrieve the rates
        date_to: until which date retrieve the dates

    Returns:
        A dict that contains for each date the rate of each currency
    """
    currencies = Currency.objects.all().values_list('code', flat=True)
    exchanges = CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency, valuation_date__gte=date_from,
        valuation_date__lte=date_to).select_related('exchanged_currency')
    dict_of_exchanges = defaultdict(dict)  # type: ignore

    for exchange in exchanges:
        dict_of_exchanges[str(exchange.valuation_date)][exchange.exchanged_currency.code] = exchange.rate_value

    delta = timedelta(days=1)
    while date_from <= date_to:
        if str(date_from) not in dict_of_exchanges:
            dict_of_exchanges[str(date_from)] = {}
        for currency in currencies:
            if currency not in dict_of_exchanges[str(date_from)]:
                exchange = _get_exchange_rate(source_currency, currency, date_from)
                dict_of_exchanges[str(date_from)][currency] = exchange.rate_value
        date_from += delta

    return dict_of_exchanges


def currency_converter(source_currency: str, exchanged_currency: str, amount: Decimal) -> dict:
    """Convert a certain amount from source_currency to exchanged_currency.

    Args:
        source_currency: The source currency in which the amount is
        exchanged_currency: The currency in which the result will be
        amount: The amount to convert

    Returns:
        A dict with the amount after exchange plus other useful info
    """
    exchanges = CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency, exchanged_currency__code=exchanged_currency)
    exchange = exchanges.order_by('-valuation_date').first()
    last_date = date.today()
    delta = timedelta(days=1)
    response = {
        'source_currency': source_currency,
        'exchanged_currency': exchanged_currency,
        f'amount_in_{source_currency}': amount,
        'rate_value': 0.0,
        'amount_after_exchange': 0
    }
    if exchange:
        start_date = exchange.valuation_date
        response.update({
                        'rate_value': exchange.rate_value,
                        'amount_after_exchange': amount * exchange.rate_value
                        })
    else:
        start_date = last_date - timedelta(days=30)
    while last_date > start_date:
        last_exchange = _get_exchange_rate(source_currency, exchanged_currency, last_date)
        if last_exchange:
            response.update({
                            'rate_value': last_exchange.rate_value,
                            'amount_after_exchange': amount * last_exchange.rate_value
                            })
            return response
        last_date -= delta
    return response


def time_weight_rate(source_currency: str, exchanged_currency: str, amount: Decimal, start_date: date) -> dict:
    """Returns the time weight rate for a certain amount converted in a certain date until now.

    Args:
        source_currency: The source currency in which the amount is
        exchanged_currency: The currency in which the result will be
        amount: The amount to convert
        start_date: From where start the time weight rate

    Returns:
        A dict with the twr and other useful information
    """
    try:
        start_date_exchange_rate = CurrencyExchangeRate.objects.get(source_currency__code=source_currency,
                                                                    exchanged_currency__code=exchanged_currency,
                                                                    valuation_date=start_date)
    except CurrencyExchangeRate.DoesNotExist:
        start_date_exchange_rate = _get_exchange_rate(source_currency, exchanged_currency, start_date)
    try:
        today_exchange_rate = CurrencyExchangeRate.objects.get(source_currency__code=source_currency,
                                                               exchanged_currency__code=exchanged_currency,
                                                               valuation_date=date.today())
    except CurrencyExchangeRate.DoesNotExist:
        today_exchange_rate = _get_exchange_rate(source_currency, exchanged_currency, date.today())
    initial_amount_exchanged = amount * start_date_exchange_rate.rate_value
    final_amount_source = initial_amount_exchanged / today_exchange_rate.rate_value
    twr = (final_amount_source - amount) / amount
    response = {
        f'initial_amount_in_{source_currency}': amount,
        f'final_amount_in_{source_currency}': final_amount_source,
        f'amount_in_{exchanged_currency}': initial_amount_exchanged,
        'initial_exchange_rate': start_date_exchange_rate.rate_value,
        'current_exchange_rate': today_exchange_rate.rate_value,
        'twr_percentage': twr * 100
    }
    return response


def _get_exchange_rate(source_currency: str, exchanged_currency: str, valuation_date: date) -> Optional[CurrencyExchangeRate]:
    for provider in CurrencyProvider.objects.order_by('priority'):
        try:
            return get_exchange_rate_data(source_currency, exchanged_currency, valuation_date, provider)
        except ProviderUnavailable:
            pass
    return None


def get_exchange_rate_data(source_currency: str, exchanged_currency: str, valuation_date: date,
                           provider: CurrencyProvider) -> CurrencyExchangeRate:
    """Returns a CurrencyExchangeRate generated with data from the given provider.

    Args:
        source_currency: The source currency to calculate rate
        exchanged_currency: The currency of which we want the rate
        valuation_date: The date of the rate requested
        provider: The provider to get the rate from

    Returns:
        CurrencyExchangeRate generated with data from the given provider

    Raises:
        ProviderUnavailable: provider is not able to respond.
    """
    adapter = Adapter(provider, source_currency, exchanged_currency, valuation_date)
    try:
        rate_value = adapter.get_exchange_rate(source_currency, exchanged_currency, valuation_date)
    except Exception as e:
        raise ProviderUnavailable(str(e))
    source_currency_obj = Currency.objects.get(code=source_currency)
    exchanged_currency_obj = Currency.objects.get(code=exchanged_currency)
    currency_exchange, _ = CurrencyExchangeRate.objects.update_or_create(
        source_currency=source_currency_obj, exchanged_currency=exchanged_currency_obj, valuation_date=valuation_date,
        defaults={'rate_value': rate_value}
    )

    revert_currency_exchange, _ = CurrencyExchangeRate.objects.update_or_create(
        source_currency=exchanged_currency_obj, exchanged_currency=source_currency_obj, valuation_date=valuation_date,
        defaults={'rate_value': 1 / rate_value}
    )
    return currency_exchange


def get_async_data(source_currency: str, exchanged_currencies: str, date_from: date, date_to: date) -> None:
    """Generate the requested data in a async way using the mock provider.

    Args:
        source_currency: The source currency to get rates
        exchanged_currencies: a string containing currency codes separated by ,
        date_from: from which date retrieve the rates
        date_to: until which date retrieve the dates
    """
    provider = CurrencyProvider.objects.filter(provider_type=CurrencyProvider.MOCK).first()
    delta = timedelta(days=1)
    queue = django_rq.get_queue('default', autocommit=True, is_async=True, default_timeout=360)
    for exchanged_currency in exchanged_currencies.split(','):
        while date_from <= date_to:
            queue.enqueue(
                get_exchange_rate_data, source_currency=source_currency, exchanged_currency=exchanged_currency,
                valuation_date=date_from, provider=provider
            )
            date_from += delta
