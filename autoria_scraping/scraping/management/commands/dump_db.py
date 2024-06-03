import os
import time
import datetime
import logging
from django.core.management.base import BaseCommand
from autoria_scraping import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Dump database'

    def add_arguments(self, parser):
        parser.add_argument('--start_time_str', type=str)

    def handle(self, *args, **kwargs):
        start_time = datetime.datetime.utcnow()
        if start_time_str := kwargs.get('start_time_str', None):
            start_time = datetime.datetime.strptime(start_time_str, '%H:%M').time()
            start_time = datetime.datetime.combine(datetime.date.today(), start_time)
            wait_seconds = (start_time - datetime.datetime.utcnow()).total_seconds()

            if wait_seconds < 0:
                wait_seconds += 24 * 3600

            logger.error(f'Очікування до {start_time} UTC. Очікування {wait_seconds} секунд.')
            time.sleep(wait_seconds)

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
