# nucoro-exchange app

## Pre-requirements
* Redis installed.

## Instalall
1. Clone the repository on your terminal
    > git clone git@github.com:rhherrera/nucoro-exchange.git
2. cd nucoro-exchange/
3. pipenv install
4. pipenv install --dev
5. In *nucoro/nucoro/settings.py* you need to change the redis password to the one of your redis server. Change *yourpassword* for your own password in the following block.
    > RQ_QUEUES = {
    >    'default': {
    >        'HOST': 'localhost',
    >        'PORT': 6379,
    >        'DB': 0,
    >        'PASSWORD': 'yourpassword',
    >        'DEFAULT_TIMEOUT': 360,
    >    },
    > }.
6. Now you need to add your FIXERIO_APIKEY. There are two ways:
    1. In *nucoro/nucoro/settings.py* change *FIXERIO_APIKEY = get_env_value('FIXERIO_APIKEY')* for *FIXERIO_APIKEY = 'Your api key'*
    2. Add an env variable on your system called FIXERIO_APIKEY with your fixer api key.
        * Take in mind that you need to have it not only at session level because you may need to use multiple terminals/tabs.
7. Now you need to enter to the pipenv
    > pipenv shell
8. Run django migrations
    > cd nucoro
    > python manage.py migrate
    * Migrate will create db structure but also will add initial providers (fixerio and mock) and supported currencies (EUR, USD, GBP, CHF).
9. Finally to be able to access to the django admin user you need to create a superuser.
    > python manage.py createsuperuser
10. Everything is up to start using the App.

## Tests and quality assurance
1. To check tests, coverage, lint and types you have nox installed as a dev package.
2. Inside the pipenv and standing on the root folder (nucoro-exchange/) you can run nox.
    > nox
    * nox will run: lint, safety, mypy, tests, pytype, coverage.
        * lint: for lint I used flake8 (you can check the conf file called .flake8)
        * safety: to check the virtual environment, requirement files, or any input from stdin for dependencies with security issues.
        * mypy: static type checker for Python that aims to combine the benefits of dynamic (or "duck") typing and static typing.
        * tests: run django tests using coverage command to generate data.
        * coverage: tool for measuring code coverage of tests.
        * pytype: checks and infers types for your Python code.
    * You can also run any of this commands separately with -s.
        > nox -s tests

## Running API and admin
* To run the server as this is not ready for production you run the developer server (you need to be standing at *nucoro-exchange/nucoro*
    > python manage.py runserver

### Admin
1. On admin (after login) you will see three models under **EXCHANGER**
    1. Currency: Where you can check the allowed currency, change them or adapt them (Mock provider only works for the current ones).
    2. Currency Providers: where the currency providers are stored.
        1. You can change the priority (0 is mayor priority, 1 less than 0 and so on)
        2. You can create a new custom provider.
            1. For doing this you need to give a name a priority (priorities are uniques so you can't have two providers with priority 0) and the code to exec.
            2. For the code must be in python, must be a function and in the placeholder of the field you will find the firm that must have that function.
    3. Currency Exchange Rates: All rates stored on the database plus a chart and the currency converter.
        1. In the list view you will see the chart that will be updated with each rate added.
        2. Also there is a button *Currency Converter* that will take you to a form so you can convert amounts into different currencies. That form has the following fields:
            * Source currency: a string representing the currency in which the amount is. Can be : USD, EUR, GBP or CHF.
            * Amount a number with decimals to convert. Ex: 9.76
            * Exchanged currencies: The currencies in which you want to see the amount (can be more than one and should be a string comma separated without spaces). Ex: USD,EUR,GBP
### API
*  The API has 3 synchonous endpoints and an asynchronous one.
* All the endpoints are under v1/ . Example: http://127.0.0.1:8000/v1/{service_you_want_to_use}?{quey_params}}

### Synchronous endpoints
1. exchange_rates: Service to retrieve a List of currency rates for a specific time period.
    * Query params:
        * date_from: date string representation with the format YY-m-d
        * date_to: date string representation with the format YY-m-d
        * source_currency: string code of the source currency. Ex: EUR
        * Example:
            > http://127.0.0.1:8000/v1/exchange_rates/?date_from=2021-03-29&date_to=2021-04-01&source_currency=EUR
2. currency_converter: Service to convert a certain amount from a currency to another.
    * Query params:
        * source_currency: string code of the source currency. Ex: EUR
        * exchanged_currency: currency in which we want the result. Ex: USD
        * amount: Amount to convert. Ex: 9.76
        * Example:
            > http://127.0.0.1:8000/v1/currency_converter/?source_currency=USD&exchanged_currency=GBP&amount=74.12
3. time-weightedror: Retrieve the TWR for a certain amount in a period from a start_date until now
    * Query params:
        * source_currency: string code of the source currency. Ex: EUR
        * exchanged_currency: Currency in which we invested. Ex: USD
        * amount: Amount we invested. Ex: 9.76
        * start_date: The date we invested with the format Y-m-d
        * Example:
            > http://127.0.0.1:8000/v1/time-weightedror/?source_currency=USD&exchanged_currency=GBP&amount=74.12&start_date=2021-04-05

### Asynchronous endpoint
* For being able to store big amounts od data (multiple rates for multiple dates) at the same time we have a async endpoint.
    * How it works: Basically the endpoint will add to a queue (in redis) the requested exchange currencies for each requested day and an async worker will do the job.
    * Because of that we need to keep the workers running in another tab (or after doing the request stop the server and run the workers), so here are the instructions.
        1. Open a new terminal and go to the folder of the repository.
        2. cd nucoro-exchange/
        3. pipenv shell
        4. cd nucoro/
        5. python manage.py rqworker default
    * generate_async_data: Adds to a queue message for retrieving all currency rate requested.
        * This endpoint only works with Mock provider.
        * Query params:
            * source_currency: string code of the source currency. Ex: EUR
            * date_from: date string representation with the format YY-m-d
            * date_to: date string representation with the format YY-m-d
            * exchanged_currencies: The currencies for which we want the rates (can be more than one and should be a string comma separated without spaces). Ex: USD,EUR,GBP
        * Example:
            > http://127.0.0.1:8000/v1/generate_async_data?date_from=2017-01-01&date_to=2017-03-27&source_currency=EUR&exchanged_currencies=USD,GBP

## Commands
* For adding multiple rates we also have a django command. This command receives a path to a csv file from where will take all the rates to add to the database.
* A csv example can be found in *nucoro/exchanger/csv_samples/add_data.csv*
* The csv format is the following: 
    > source_currency,exchange_currency,date,rate
    > An example:
    > EUR,GBP,2019-12-31,1.12
* To run the command you must be inside the pipenv and standing on *nucoro-exchange/nucoro* and run:
    > python manage.py batch_store_rates <path-to-csv-file>
    > Example:
    > python manage.py batch_store_rates exchanger/csv_samples/add_data.csv

## Improvements
* Auto-contain the app on a docker container, so setup would be easier.
* Add sphinx to have a centralized api-docs
* Improve custom views (mostly the one of Currency Exchange Rates)
* Add more tests to improve coverage (tests of endpoints, command would be desirable)
