"""Models module."""
from django.db import models  # type: ignore


class Currency(models.Model):
    """Currency model."""
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20, db_index=True)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.code


class CurrencyExchangeRate(models.Model):
    """CurrencyExchangeRate model."""
    source_currency = models.ForeignKey(Currency, related_name='exchanges', on_delete=models.CASCADE)
    exchanged_currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(db_index=True, decimal_places=6, max_digits=18)

    class Meta:
        """Meta class."""
        constraints = [
            models.UniqueConstraint(fields=['source_currency', 'exchanged_currency', 'valuation_date'], name='unique exchange')
        ]


class CurrencyProvider(models.Model):
    """CurrencyProvider model."""
    FIXERIO = 'fixerio'
    MOCK = 'mock'
    PLUGIN = 'plugin'
    PROVIDER_CHOICES = [
        (FIXERIO, 'Fixer Io'),
        (MOCK, 'Mock'),
        (PLUGIN, 'Plugin')
    ]

    priority = models.IntegerField(unique=True)
    name = models.CharField(max_length=40)
    provider_type = models.CharField(
        max_length=7,
        choices=PROVIDER_CHOICES,
        default=FIXERIO)
    exchange_rate_code = models.TextField(blank=True, null=True)
