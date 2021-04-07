"""Admin module."""
import decimal
import json
from typing import Any

from django import forms  # type: ignore
from django.contrib import admin  # type: ignore
from django.core.serializers.json import DjangoJSONEncoder  # type: ignore
from django.http import HttpResponse  # type: ignore
from django.template import loader  # type: ignore

from exchanger.interactors import currency_converter
from exchanger.models import Currency, CurrencyExchangeRate, CurrencyProvider


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Admin for Currency."""

    list_display = ("code",)
    ordering = ("code",)


@admin.register(CurrencyProvider)
class CurrencyProviderAdmin(admin.ModelAdmin):
    """Admin for CurrencyProvider."""

    list_display = ("name", "provider_type", "priority")
    ordering = ("priority",)

    def get_form(self, request: Any, obj: Any = None, **kwargs) -> forms.Form:
        """Function that returns an exchange rate from a certain provider.

        Args:
            request: The request object
            obj: The object
            kwargs: extra data for the form

        Returns:
            a custom form
        """
        placeholder = """
        define a function with the signature that returns a float or Decimal:
        def custom_exchange_rate(valuation_date, source_currency, exchanged_currency) -> float:
            ....
        """
        kwargs['widgets'] = {
            'exchange_rate_code': forms.Textarea(attrs={'placeholder': placeholder, 'rows': 20, 'cols': 120})
        }
        return super().get_form(request, obj, **kwargs)


@admin.register(CurrencyExchangeRate)
class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    """Admin for CurrencyExchangeRate."""

    fields = ("source_currency", "exchanged_currency", "valuation_date", "rate_value")
    list_display = ("get_source_currency", "get_exchanged_currency", "rate_value", "valuation_date")
    ordering = ("-valuation_date",)

    def get_source_currency(self, obj: CurrencyExchangeRate) -> str:
        """Function that returns the code of the source_currency.

        Args:
            obj: The object

        Returns:
            the source currency code
        """
        return obj.source_currency.code
    get_source_currency.short_description = 'Source Currency'  # type: ignore
    get_source_currency.admin_order_field = 'source_currency__code'  # type: ignore

    def get_exchanged_currency(self, obj: CurrencyExchangeRate) -> str:
        """Function that returns the code of the exchanged_currency.

        Args:
            obj: The object

        Returns:
            the exchanged_currency code
        """
        return obj.exchanged_currency.code
    get_exchanged_currency.short_description = 'Exchange Currency'  # type: ignore
    get_exchanged_currency.admin_order_field = 'exchange_currency__code'  # type: ignore

    def changelist_view(self, request: Any, extra_context: Any = None) -> Any:
        """Change list view custom to contain the chart.

        Args:
            request: The request object
            extra_context: The extra context

        Returns:
            render the proper view
        """
        chart_query = CurrencyExchangeRate.objects.filter(
            source_currency__code='EUR').order_by(
                'valuation_date', 'exchanged_currency__code').select_related('exchanged_currency')
        chart_data = None
        data = {}
        codes = [curr.code for curr in Currency.objects.all()]
        for elem in chart_query:
            if str(elem.valuation_date) not in data:
                data[str(elem.valuation_date)] = {code: None for code in codes}
            data[str(elem.valuation_date)][elem.exchanged_currency.code] = elem.rate_value
        datasets = {code: [] for code in codes}  # type: ignore
        labels = []
        for d in data:
            for code in codes:
                datasets[code].append(data[d][code])
            labels.append(d)
        chart_data = {'labels': labels, 'datasets': datasets}

        # Serialize and attach the chart data to the template context
        as_json = json.dumps(chart_data, cls=DjangoJSONEncoder)
        extra_context = extra_context or {"chart_data": as_json}

        # Call the superclass changelist_view to render the page
        return super().changelist_view(request, extra_context=extra_context)


class ConverterForm(forms.Form):
    """Form used for currency converter view."""

    source_currency = forms.CharField(max_length=30)
    amount = forms.DecimalField()
    exchanged_currencies = forms.CharField(max_length=40)

    def clean(self) -> None:
        """Clean the form fields.

        Raises:
            ValidationError: the form is invalid
        """
        cleaned_data = super(ConverterForm, self).clean()
        source_currency = cleaned_data.get('source_currency')
        amount = cleaned_data.get('amount')
        exchanged_currencies = cleaned_data.get('exchanged_currencies')
        if not source_currency and not amount and not exchanged_currencies:
            raise forms.ValidationError('You have to write something!')


def currency_converter_admin(request: Any) -> HttpResponse:
    """View of the currency converter admin.

    Args:
        request: The request object

    Returns:
        the currency converter view
    """
    data = []
    if request.method == 'POST':
        form = ConverterForm(request.POST)
        if form.is_valid():
            for exchanged_currency in form['exchanged_currencies'].value().split(','):
                data.append(currency_converter(
                    form['source_currency'].value(), exchanged_currency, decimal.Decimal(form['amount'].value())))
    else:
        form = ConverterForm()

    context = {
        'title': 'Currency converter',
        'anything': 'casa',
        'form': form,
        'data': data

    }

    template = loader.get_template('admin/currencyconverter.html')
    return HttpResponse(template.render(context, request))
