"""Views module."""
from datetime import datetime
import decimal
from typing import Any

from rest_framework import status  # type: ignore
from rest_framework.decorators import api_view  # type: ignore
from rest_framework.response import Response  # type: ignore

from exchanger.interactors import currency_converter, get_async_data, get_exchange_rates, time_weight_rate


@api_view(['GET'])
def get_exchange_rates_view(request: Any) -> Response:
    """Retrieve a list of currency rates for a specific time period.

    Args:
        request: the request object.

    Returns:
        A rest framework Response
    """
    source_currency = request.query_params.get('source_currency')
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')
    try:
        if source_currency and date_from_str and date_to_str:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            results = get_exchange_rates(source_currency, date_from, date_to)
            return Response(results)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def currency_converter_view(request: Any) -> Response:
    """Retrieve an amount converted to a specified currency.

    Args:
        request: the request object.

    Returns:
        A rest framework Response
    """
    source_currency = request.query_params.get('source_currency')
    exchanged_currency = request.query_params.get('exchanged_currency')
    amount = request.query_params.get('amount')
    try:
        if source_currency and exchanged_currency and amount:
            results = currency_converter(source_currency, exchanged_currency, decimal.Decimal(amount))
            return Response(results)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def time_weight_rate_view(request: Any) -> Response:
    """Retrieve the TWR for a certain amount in a defined period.

    Args:
        request: the request object.

    Returns:
        A rest framework Response

    """
    source_currency = request.query_params.get('source_currency')
    exchanged_currency = request.query_params.get('exchanged_currency')
    amount = request.query_params.get('amount')
    start_date_str = request.query_params.get('start_date')
    try:
        if source_currency and exchanged_currency and amount and start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            results = time_weight_rate(source_currency, exchanged_currency, decimal.Decimal(amount), start_date)
            return Response(results)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def generate_async_data(request: Any) -> Response:
    """Retrieve a list of currency rates for a specific time period.

    Args:
        request: the request object.

    Returns:
        A rest framework Response

    """
    source_currency = request.query_params.get('source_currency')
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')
    exchanged_currencies = request.query_params.get('exchanged_currencies')
    try:
        if source_currency and date_from_str and date_to_str and exchanged_currencies:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            get_async_data(source_currency, exchanged_currencies, date_from, date_to)
            return Response('Getting async data is being executed.')
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
