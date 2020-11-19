from django.db import models
from django.db.models import Sum, QuerySet, Subquery, Count, Max
import datetime
from .config import LAST_UPDATED_DATE,LAST_UPDATED_DATE_STR

# Create your models here.
from django.db.models.functions import TruncDate, TruncMonth, Trunc


class country(models.Model):
    city=models.CharField(max_length=100,null=True)
    state = models.CharField(max_length=100,null=True)
    country=models.CharField(max_length=100)
    lat=models.DecimalField(max_length=100,decimal_places=4,max_digits=7)
    lng=models.DecimalField(max_length=100,decimal_places=4,max_digits=7)

class country_total_data(models.Model):
    Date=models.DateTimeField('Added Date',null=True)
    Country=models.CharField(max_length=100)
    Confirmed=models.IntegerField(default=0)
    Recovered=models.IntegerField(default=0)
    Deaths=models.IntegerField(default=0)

class worldwide_aggregated_data(models.Model):
    Date = models.DateField('Added Date', null=True)
    Confirmed = models.IntegerField(default=0)
    Recovered = models.IntegerField(default=0)
    Deaths = models.IntegerField(default=0)
    IncreaseRate=models.DecimalField(max_length=100,decimal_places=4,max_digits=7)

class corona_data(models.Model):
    state=models.CharField(max_length=100)
    country=models.CharField(max_length=100)
    confirmed=models.IntegerField(default=0)
    recovered=models.IntegerField(default=0)
    deaths=models.IntegerField(default=0)
    updated_at=models.DateTimeField('Updated Date',null=True)
    lat = models.DecimalField(max_length=100, decimal_places=4, max_digits=7)
    lng = models.DecimalField(max_length=100, decimal_places=4, max_digits=7)

    def total_countries_confirmed(self,country_name):
        if country_name:
            return corona_data.objects.all().filter(country=country_name,updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, LAST_UPDATED_DATE.day)).aggregate(total_cases=Sum('confirmed'))
        else:
            return corona_data.objects.filter(updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, LAST_UPDATED_DATE.day)).all().aggregate(total_cases=Sum('confirmed'))

    def total_countries_deaths(self,country_name):
        if country_name:
            return corona_data.objects.all().filter(country=country_name,updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, LAST_UPDATED_DATE.day)).aggregate(total_cases=Sum('deaths'))
        else:
            return corona_data.objects.filter(updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, LAST_UPDATED_DATE.day)).all().aggregate(total_cases=Sum('deaths'))

    def total_countries_recovery(self,country_name):
        if country_name:
            return corona_data.objects.all().filter(country=country_name,updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, 23)).aggregate(total_cases=Sum('recovered'))
        else:
            return corona_data.objects.filter(updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, 23)).all().aggregate(total_cases=Sum('recovered'))

    def all_countries_confirmed(self,country_name):
        total_Cases= corona_data.objects.filter(updated_at__date=datetime.date(LAST_UPDATED_DATE.year, LAST_UPDATED_DATE.month, LAST_UPDATED_DATE.day)).values('country').annotate(total_cases=Sum('confirmed'))
        if country_name:
            total_Cases=total_Cases.filter(country=country_name)
        return total_Cases

    def map_data(self):
        #return corona_data.objects.filter(updated_at__date=datetime.date(2020, 3, 23)).select_related('country','state','lat','lng').values('country','state','lat','lng').annotate(total_cases=Sum('confirmed'))

        return corona_data.objects.raw(
            'SELECT corona_corona_data.id, corona_corona_data.country,corona_corona_data.state,lat,lng,sum(confirmed) as total_cases '
            ' FROM corona_corona_data '
            ' WHERE updated_at=%s '
            ' GROUP BY corona_corona_data.country,corona_corona_data.state,lat,lng'
            ' HAVING sum(confirmed)>0',[LAST_UPDATED_DATE_STR])

    def monthly_data(self):
        return corona_data.objects.raw('SELECT corona_corona_data.id, sum(confirmed) as total_cases'
                                       ' FROM corona_corona_data '
                                       ' GROUP BY DATE_FORMAT(corona_corona_data.updated_at, "%Y-%m") as month_Dates'                                       
                                       ' HAVING sum(confirmed)>0')



