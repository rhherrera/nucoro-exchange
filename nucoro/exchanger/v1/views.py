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

    Description:
        parameters:
            name: date_from
            in: query
            type: string
            description: Date string representation with the format Y-m-d
            name: date_to
            in: query
            type: string
            description: Date string representation with the format Y-m-d
            name: source_currency
            in: query
            type: string
            description: String code of the source currency. Ex: EUR

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

    Description:
        parameters:
            name: source_currency
            in: query
            type: string
            description: String code of the source currency. Ex: EUR
            name: exchanged_currency
            in: query
            type: string
            description: Currency in which we want the result. Ex: USD
            name: amount
            in: query
            type: decimal
            description: Amount to convert. Ex: 9.76

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
    """Retrieve the TWR for a certain amount in a period from a start_date until now.

    Args:
        request: the request object.

    Description:
        parameters:
            name: source_currency
            in: query
            type: string
            description: String code of the source currency. Ex: EUR
            name: exchanged_currency
            in: query
            type: string
            description: Currency in which we invested. Ex: USD
            name: amount
            in: query
            type: decimal
            description: Amount we invested. Ex: 9.76
            name: start_date
            in: query
            type: string
            description: The date we invested with the format Y-m-d


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

    Description:
        parameters:
            name: source_currency
            in: query
            type: string
            description: String code of the source currency. Ex: EUR
            name: date_from
            in: query
            type: string
            description: Date string representation with the format Y-m-d
            name: date_to
            in: query
            type: string
            description: Date string representation with the format Y-m-d
            name: exchanged_currencies
            in: query
            type: string
            description: The currencies for which we want the rates (can be more than one). Ex: USD,EUR,GBP


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
