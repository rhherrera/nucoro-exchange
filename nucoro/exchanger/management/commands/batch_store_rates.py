"""Command to batch store currency exchanges."""
import csv
from datetime import datetime
import decimal

from django.core.management.base import ArgumentParser, BaseCommand
from django.db import transaction

from exchanger.models import Currency, CurrencyExchangeRate


class Command(BaseCommand):
    """Command to add a list of currency exchanges from a CSV."""
    help = 'Add a list of currency exchanges from a CSV.'

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Function to parse csv_path argument.

        Args:
            parser: the argument parser
        """
        parser.add_argument('csv_path', type=str, help='path to the csv file.')

    def handle(self, *args, **kwargs) -> None:
        """Function that handles the command.

        Args:
            args: Unused
            kwargs: The extra data to add to the execution entity
        """
        csv_path = kwargs['csv_path']
        added_or_updated_rates = 0
        try:
            with transaction.atomic():
                currencies = {curr.code: curr for curr in Currency.objects.all()}
                with open(csv_path) as csv_file:
                    csv_reader = csv.reader(csv_file, delimiter=',')
                    for row in csv_reader:
                        source_curr = currencies[row[0]]
                        exchange_curr = currencies[row[1]]
                        valuation_date = datetime.strptime(row[2], '%Y-%m-%d').date()
                        rate_value = decimal.Decimal(row[3])
                        currency_exchange, _ = CurrencyExchangeRate.objects.update_or_create(
                            source_currency=source_curr, exchanged_currency=exchange_curr, valuation_date=valuation_date,
                            defaults={'rate_value': rate_value}
                        )
                        added_or_updated_rates += 1
            print(f'{added_or_updated_rates} where added or updated')
        except Exception as e:
            print('Something went wrong')
            print(str(e))
