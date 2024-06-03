# autoria_scraping
## Використані інструменти:
- контейнеризація: Docker, Docker-compose
- основний фреймвок: Django
- БД: PostgreSQL (основна)
- Site scraping: BeautifulSoup
- автотестування: Pytest
- UserAgent: fake_useragent
- адміністрування БД: adminer

## Додаткові пояснення
- Формат часу системи - UTC.
- Запуск скрапінгу всього сайту може тривати довго.
- Запуск скрапінгу реалізований як Django команди.
- Був доданий генератор UserAgent, щоб зменшити вірогідність блокування зі сторони сайту.
- Для зменшення навантаження на систему збереження до БД відбувається частинами по 200 записів за раз.
- Знайдена можливість пошуку та збереження зображень в HD якості. 
- За кожним оголошенням всі наявні зображення зберігаються списком. 

## Запуск проекту 
- git clone https://github.com/kolesnikdi/DataOx.git
- cd .\DataOx\autoria_scraping
- docker-compose up --build
- Запуск скрапінгу всього сайту. Термінал Docker -> autoria_scraping -> web-1 `python manage.py run_autoria_scraping `
- Запуск скрапінгу всього сайту з дампом БД в кінці процесу. Термінал Docker -> autoria_scraping -> web-1 `python manage.py run_autoria_scraping --dump=True`
- Запуск скрапінгу перших 10 сторінок. Термінал Docker -> autoria_scraping -> web-1 `python manage.py run_autoria_scraping --pages=10`
- Запуск скрапінгу перших 10 сторінок з дампом БД в кінці процесу. Термінал Docker -> autoria_scraping -> web-1 `python manage.py run_autoria_scraping --pages=10 --dump=True`
- Запуск скрапінгу перших 10 сторінок з дампом БД в кінці процесу та активація щоденого автоматичного запуску у вказаний час. Термінал Docker -> autoria_scraping -> web-1 `python manage.py run_autoria_scraping --pages=10 --dump=True --start_time_str='21:00'`
- Запуск дампe БД. Термінал Docker -> autoria_scraping -> web-1 `python manage.py dump_db`
- Запуск дампe БД та активація щоденого автоматичного запуску у вказаний час. Термінал Docker -> autoria_scraping -> web-1 `python manage.py dump_db --start_time_str='21:00'`
- Запуск Тесту. Скрапінг 10 сторінок з дампом БД та повторний дамп БД Термінал Docker -> autoria_scraping -> web-1 `pytest`


## Endpoints
### [Adminer](http://127.0.0.1:8082) Логін та Пароль в файлі .env
