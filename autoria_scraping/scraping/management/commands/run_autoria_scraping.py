import os
import re
import time
import json
import logging
import datetime
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests import get

from autoria_scraping import settings
from scraping.models import UsedCar

logger = logging.getLogger(__name__)


class UsedCarScraping:
    __slots__ = ('max_pages', 'page', 'accept', 'not_found', 'too_many_requests', 'maine_url', 'check_url',
                 'phones_url', 'temporary_mobile', 'retry_count', 'response', 'maine_html', 'total_ads', 'start_time',
                 'ads', 'ads_to_save')

    def __init__(self, pages=None):
        self.max_pages = pages
        self.page = {'page': 1}
        self.accept = 200
        self.not_found = 404
        self.too_many_requests = 429
        self.maine_url = 'https://auto.ria.com/uk/car/used/'
        self.check_url = 'https://auto.ria.com/uk/auto_'
        self.check_url = 'https://auto.ria.com/uk/auto_'
        self.phones_url = 'https://auto.ria.com/users/phones/'
        self.temporary_mobile = '+380633334455'
        self.retry_count = 0
        self.response = self.make_request(self.maine_url, self.page)
        if self.response:
            self.maine_html = BeautifulSoup(self.response, 'html.parser')
            self.total_ads = re.search(r'Number\((\d+)\)', self.maine_html.find('script', text=re.compile(
                r'window.ria.server.resultsCount')).string).group(1)
            self.start_time = datetime.datetime.utcnow()
            logger.error(f'Початок роботи {self.start_time}. Знайдено оголошень {self.total_ads}')
        self.ads = None
        self.ads_to_save = []

    def make_request(self, url, params=None, headers=None):
        response = get(url, params=params, headers=headers)
        if response.status_code == self.accept:
            return response.content
        if response.status_code == self.not_found:
            logger.error(f'Помилка в {url}')
            return False
        if response.status_code == self.too_many_requests:
            if self.retry_count <= 5:
                time.sleep(2)
                self.retry_count += 1
                return self.make_request(url, params=params, headers=headers)
            else:
                logger.error(f'Запитуваний {url} перевантажений')
                return False
        else:
            logger.error(f'Відповідь на  {url} {response.status_code}')
            return False

    def get_modile(self, data, ad_id, header, ad_url):
        data_hash = None
        data_expires = None
        script_tags = data.find_all('script')
        for script_tag in script_tags:
            data_hash = script_tag.get('data-hash', None)
            data_expires = script_tag.get('data-expires', None)
            if data_hash and data_expires:
                break
        if data_hash is not None and data_expires is not None:
            params = {'hash': data_hash, 'expires': data_expires}
            if response := self.make_request(self.phones_url + ad_id, params=params, headers=header):
                response.decode('utf-8')
                return json.loads(response)['formattedPhoneNumber']
            else:
                logger.error(f'Проблема з доступом до мобільного за посиланням {ad_url}')
                return self.temporary_mobile
        else:
            logger.error(f'Проблема з доступом до data_hash та мобільного за посиланням {ad_url}')
            return self.temporary_mobile

    def start_scraping(self):
        if self.max_pages and self.page['page'] == self.max_pages:
            return False
        if self.page['page'] >= 2:
            self.response = self.make_request(self.maine_url, self.page)
            if self.response:
                self.maine_html = BeautifulSoup(self.response, 'html.parser')
        if not self.response:
            return False
        self.ads = self.maine_html.find_all('a', class_='m-link-ticket', href=True)
        if self.ads:
            header = {'User-Agent': UserAgent().random}
            for ad in self.ads:
                if self.check_url in ad['href']:
                    if response := self.make_request(ad['href']):
                        ad_data = BeautifulSoup(response, 'html.parser')
                        ad_id = ad['href'].split('_')[-1].split('.')[0]
                        price_usd = ad_data.find('span', class_='price_value')
                        odometer = ad_data.find('div', class_='bold dhide')
                        if odometer:
                            odometer = re.findall(r'\d+', odometer.text)
                        username = ad_data.find('div', class_='mt-10 mb-10')
                        car_number = ad_data.find('span', class_='state-num ua')
                        if car_number:
                            car_number = re.findall(r'[A-Z]{2} \d{4} [A-Z]{2}', car_number.text)
                        car_vin = ad_data.find('span', class_='label-vin')
                        unique_image = {source['srcset'].replace('s.webp', 'hd.webp') for source in
                                        ad_data.find_all('source', srcset=True) if 's.webp' in source['srcset']}
                        data = {
                            'url': ad['href'],
                            'title': ad_data.find('h1', class_='head', title=True)['title'],
                            'price_usd': int(re.sub(r'[^\d]', '', price_usd.strong.text) if price_usd else '0'),
                            'odometer': int(odometer[0] if odometer else 0) * 1000,
                            'username': username.text.split(':')[1].strip() if username else 'no_username',
                            'phone_number': self.get_modile(ad_data, ad_id, header, ad['href']),
                            'image_url': list(unique_image),
                            'images_count': len(unique_image),
                            'car_number': car_number[0] if car_number else '',
                            'car_vin': car_vin.text if car_vin else '',
                        }
                        self.ads_to_save.append(UsedCar(**data))

            self.page['page'] += 1
            return self.start_scraping()
        else:
            logger.error(
                f'Завершення роботи {datetime.datetime.utcnow()}. Опрацьовано оголошень {len(self.ads_to_save)}')


class Command(BaseCommand):
    help = 'Scraping AutoRia'

    def add_arguments(self, parser):
        parser.add_argument('--start_time_str', type=str)
        parser.add_argument('--pages', type=int)
        parser.add_argument('--dump', type=bool)

    def handle(self, *args, **kwargs):
        pages = kwargs.get('pages', None)
        dump = kwargs.get('dump', None)

        start_time = datetime.datetime.utcnow()
        if start_time_str := kwargs.get('start_time_str', None):
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            start_time = datetime.datetime.combine(datetime.date.today(), start_time)
            wait_seconds = (start_time - datetime.datetime.utcnow()).total_seconds()

            if wait_seconds < 0:
                wait_seconds += 24 * 3600

            logger.error(f'Очікування до {start_time} UTC. Очікування {wait_seconds} секунд.')
            time.sleep(wait_seconds)

        auto_ria = False
        try:
            auto_ria = UsedCarScraping(pages)
            auto_ria.start_scraping()
            self.stdout.write(self.style.SUCCESS('Successfully scraped auto ria.'))
        except Exception as e:
            self.stdout.write(self.style.SUCCESS(f'Error while executing UsedCarScraping: {str(e)}.'))
            logger.error(f'Помилка при виконанні UsedCarScraping: {str(e)}')

        if auto_ria and auto_ria.ads_to_save:
            try:
                UsedCar.objects.bulk_create(auto_ria.ads_to_save, batch_size=200, update_conflicts=True,
                                            update_fields=['price_usd', 'odometer', 'phone_number', 'image_url',
                                                           'car_number',
                                                           'car_vin'], unique_fields=['url'])
                self.stdout.write(self.style.SUCCESS('Successfully write data to db.'))
                logger.error(f'БД оновлена о {datetime.datetime.utcnow()}')
            except Exception as e:
                self.stdout.write(self.style.SUCCESS(f'Error saving records: {str(e)}.'))
                logger.error(f'Помилка при збереженні записів: {str(e)}')

        if dump:
            try:
                path = os.path.join(settings.BASE_DIR, 'dumps', f'dump_{start_time.strftime('%Y%m%d_%H%M%S')}.dump')
                if not os.path.exists(os.path.dirname(path)):
                    os.makedirs(os.path.dirname(path))
                db_user = settings.DATABASES['default']['USER']
                db_name = settings.DATABASES['default']['NAME']
                os.system(f'docker exec -t autoria_scraping-db-1 pg_dump -U {db_user} -d {db_name} -Fc > {path}')
                self.stdout.write(self.style.SUCCESS(f'Successfully dumped db to {path}'))
            except Exception as e:
                self.stdout.write(self.style.SUCCESS(f'Error while dump db: {str(e)}.'))
                logger.error(f'Помилка під час дампу бд: {str(e)}')

        if start_time_str:
            self.handle(start_time_str)
