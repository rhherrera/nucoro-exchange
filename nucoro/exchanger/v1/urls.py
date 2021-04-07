"""Nucoro URL Configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path  # type: ignore

from exchanger.v1 import views


urlpatterns = [
    path('exchange_rates/', views.get_exchange_rates_view),
    path('currency_converter/', views.currency_converter_view),
    path('time-weightedror/', views.time_weight_rate_view),
    path('generate_async_data', views.generate_async_data),
]
