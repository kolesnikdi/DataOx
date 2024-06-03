import pytest
from scraping.models import UsedCar
from django.core.management import call_command


@pytest.mark.django_db
def test_perform_scraping():
    call_command('run_autoria_scraping', pages=10, dump=True)
    call_command('dump_db')
    assert len(UsedCar.objects.all()) > 70
