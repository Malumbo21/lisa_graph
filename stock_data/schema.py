import traceback
import graphene
from datetime import datetime, timedelta
from stock_data.models import StockData
from django.db import models
from django.db.models.functions import Lag, TruncDate, ExtractWeek, ExtractMonth, ExtractYear, FirstValue
from django.db.models import F, Value, Window, Min, Max, ExpressionWrapper, fields, OuterRef, Subquery, Q, Sum
from scraper import scraper
from graphene_django import DjangoObjectType

class StockDataType(DjangoObjectType):
    class Meta:
        model = StockData
class WeeklyHighLowType(graphene.ObjectType):
    week_start = graphene.String()
    week_end = graphene.String()
    first_record = graphene.String()
    last_record = graphene.String()
    weekly_high = graphene.Float()
    weekly_low = graphene.Float()
class ScraperResultType(graphene.ObjectType):
    message = graphene.String()
class StockDataChangeType(graphene.ObjectType):
    instrument = graphene.String()
    start_date = graphene.String()
    end_date = graphene.String()
    total_change = graphene.Float()

class FluctuationType(graphene.ObjectType):
    id = graphene.Int()
    instrument = graphene.String()
    total_price_diff = graphene.Float()
    date = graphene.Date()
class Query(graphene.ObjectType):
    stock_data = graphene.List(StockDataType, start=graphene.String(), end=graphene.String(), symbol=graphene.String(), single_date=graphene.Boolean(), date=graphene.String(), latest=graphene.Boolean())
    instruments = graphene.List(graphene.String)
    top_gainers = graphene.List(StockDataChangeType, n=graphene.Int(), day=graphene.Boolean(), week=graphene.Boolean(), month=graphene.Boolean(), year=graphene.Boolean(), date=graphene.String())
    top_losers = graphene.List(StockDataChangeType, n=graphene.Int(), day=graphene.Boolean(), week=graphene.Boolean(), month=graphene.Boolean(), year=graphene.Boolean())
    weekly_high_low = graphene.List(WeeklyHighLowType, instrument=graphene.String(), year=graphene.Int(), month=graphene.Int(), n=graphene.Int())
    changes = graphene.Field(StockDataChangeType, instrument=graphene.String(), year=graphene.Int(), month=graphene.Int(), week=graphene.Int(), n=graphene.Int())
    update_data = graphene.Field(ScraperResultType)
    @staticmethod
    def get_total_change(d_1,d_2, instrument):
        try:
            s = StockData.objects.get(date=d_1.strftime('%Y-%m-%d'), instrument=instrument)
            e = StockData.objects.get(date=d_2.strftime('%Y-%m-%d'), instrument=instrument)
            
            change = e.closing_price - s.closing_price
            print(change)
            return change
        except Exception as e:
            print(e)
    def resolve_update_data(self, info):
        s = scraper.Scrape()
        s.run()
        return {"message": "data updated successfully"}
    def resolve_changes(self, info, instrument=None, year=None, month=None, week=None):
        # Filtering based on the given instrument, year, month, and week
        try:
            data = StockData.objects.all()
            if instrument is None:
                raise Exception("Instrument required")
            if instrument:
                data = data.filter(instrument=instrument)
            if year:
                data = data.filter(date__year=year)
            if month:
                data = data.filter(date__month=month)
            if week:
                data = data.filter(date__week=week)
            # Group data by start_date and end_date
            grouped_data = data.values('instrument').annotate(
                start_date=Min('date'),
                end_date=Max('date'),
                total_change=ExpressionWrapper(
                    F('closing_price') - F('opening_price'),
                    output_field=fields.DecimalField()
                )
            ).order_by('start_date', 'end_date')
            result = grouped_data.first()
            

            changes_data = {
                    'instrument': instrument,
                    'start_date': result['start_date'].strftime('%Y-%m-%d'),
                    'end_date': result['end_date'].strftime('%Y-%m-%d'),
                    'total_change': Query.get_total_change(result['start_date'], result['end_date'], instrument),
                }
            
            return changes_data
        except Exception as e:
            print(e)
            print(traceback.format_exc())
    def resolve_weekly_high_low(self, info, instrument=None, year=None, month=None, start_date=None, end_date=None, n=None):
        data = StockData.objects.all()

        # Filter by instrument, year, and month
        if instrument:
            data = data.filter(instrument=instrument)
        if year:
            data = data.filter(date__year=year)
        if month:
            data = data.filter(date__month=month)

        # Add date range filtering to the queryset
        if start_date and end_date:
            data = data.filter(date__range=[start_date, end_date])

        # Annotate the queryset with the week_start and previous_closing_price
        data = data.annotate(
            week_start=ExpressionWrapper(
                F('date') - (F('date__week_day') + 1) * Value(timedelta(days=1)),
                output_field=fields.DateField()
            ),
            week_end=ExpressionWrapper(
                F('week_start') + Value(timedelta(days=6)),
                output_field=fields.DateField()
            ),
            previous_closing_price=F('closing_price')  # Adjust this if necessary
        )

        # Calculate the price difference for each week
        data = data.annotate(
            price_diff=ExpressionWrapper(
                F('closing_price') - F('previous_closing_price'),
                output_field=fields.DecimalField()
            )
        )

        # Group data by week_start and get the first and last records for each week
        grouped_data = data.values('week_start', 'week_end').annotate(
            first_record=Min('date'),
            last_record=Max('date'),
            weekly_high=Max('closing_price'),
            weekly_low=Min('closing_price'),
        ).order_by('week_start')

        # Get the weekly high and low for each week
        weekly_high_low_data = []
        for record in grouped_data:
            week_data = data.filter(week_start=record['week_start'], week_end=record['week_end'])
            weekly_high = week_data.aggregate(Max('closing_price'))['closing_price__max']
            weekly_low = week_data.aggregate(Min('closing_price'))['closing_price__min']

            weekly_high_low_data.append({
                'week_start': record['week_start'].strftime('%Y-%m-%d'),
                'week_end': record['week_end'].strftime('%Y-%m-%d'),
                'first_record': record['first_record'].strftime('%Y-%m-%d'),
                'last_record': record['last_record'].strftime('%Y-%m-%d'),
                'weekly_high': float(weekly_high),
                'weekly_low': float(weekly_low),
            })

        # Optionally, get the top N weekly differences
        if n is not None:
            weekly_high_low_data = sorted(weekly_high_low_data, key=lambda x: x['weekly_high'] - x['weekly_low'], reverse=True)[:n]

        return weekly_high_low_data
    def resolve_stock_data(self, info, start=None, end=None, symbol=None, single_date=False, date=None, latest=False):
        data = StockData.objects.all()

        if latest:
            latest_date = StockData.objects.aggregate(Max('date'))['date__max']
            data = data.filter(date=latest_date)

        if symbol:
            data = data.filter(instrument=symbol)
        if single_date:
            if date is None:
                raise Exception(f"Date cannot be none when single_date=True")
            data = data.filter(date__exact=date)
        if start:
            if end is None:
                starttime = datetime.strptime(start, "%Y-%m-%d").date()
                data = data.annotate(start_date=Cast(F('date'), models.DateField()))
                data = data.filter(start_date__gte=starttime)
            else:
                data = data.filter(date__range=(start, end))
        if end:
            if start is None:
                endtime = datetime.strptime(end, "%Y-%m-%d").date()
                data = data.filter(date__lte=endtime)

        return data
    def resolve_top_gaines(self, info, n=None, day=False, week=False, month=False, year=False, date=None):
        instruments = StockData.objects.values("instrument").distinct()
        instrument_names = [item["instrument"] for item in instruments]
        instrument_names = list(set(instrument_names))
        gaines = []
        data = StockData.objects.all()
        for instrument in instrument_names:
            if not any([day, week, month, year]):
                raise Exception("Error: Set at least one of the timeframe options (day, week, month, year) to True")

            max_date = StockData.objects.aggregate(Max('date'))['date__max']
            if max_date is None:
                return []

            data = data.filter(instrument=instrument)

            if day:
                data = data.filter(date=max_date)
            elif week:
                start_of_week = max_date - timedelta(days=max_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                data = data.filter(date__range=[start_of_week, end_of_week])
            elif month:
                data = data.filter(date__month=max_date.month, date__year=max_date.year)
            elif year:
                data = data.filter(date__year=max_date.year)

            if not data.exists():
                return []

            grouped_data = data.values('instrument').annotate(
                start_date=Min('date'),
                end_date=Max('date'),
                total_change=ExpressionWrapper(
                    F('closing_price') - F('opening_price'),
                    output_field=fields.DecimalField()
                )
            ).order_by('start_date', 'end_date')
            result = grouped_data.first()
            

            changes_data = {
                    'instrument': instrument,
                    'start_date': result['start_date'].strftime('%Y-%m-%d'),
                    'end_date': result['end_date'].strftime('%Y-%m-%d'),
                    'total_change': Query.get_total_change(result['start_date'], result['end_date'], instrument),
            }
            gaines.append(changes_data)
        gaines = [g for g in gaines if g['total_change']>0]
        sorted_gains = sorted(gaines, key=lambda x: x['total_change'])
        print(sorted_gains)
        return sorted_gains
    def resolve_top_losers(self, info, n=None, day=False, week=False, month=False, year=False, date=None):
        instruments = StockData.objects.values("instrument").distinct()
        instrument_names = [item["instrument"] for item in instruments]
        instrument_names = list(set(instrument_names))
        gaines = []
        data = StockData.objects.all()
        for instrument in instrument_names:
            if not any([day, week, month, year]):
                raise Exception("Error: Set at least one of the timeframe options (day, week, month, year) to True")

            max_date = StockData.objects.aggregate(Max('date'))['date__max']
            if max_date is None:
                return []

            data = data.filter(instrument=instrument)

            if day:
                data = data.filter(date=max_date)
            elif week:
                start_of_week = max_date - timedelta(days=max_date.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                data = data.filter(date__range=[start_of_week, end_of_week])
            elif month:
                data = data.filter(date__month=max_date.month, date__year=max_date.year)
            elif year:
                data = data.filter(date__year=max_date.year)

            if not data.exists():
                return []

            grouped_data = data.values('instrument').annotate(
                start_date=Min('date'),
                end_date=Max('date'),
                total_change=ExpressionWrapper(
                    F('closing_price') - F('opening_price'),
                    output_field=fields.DecimalField()
                )
            ).order_by('start_date', 'end_date')
            result = grouped_data.first()
            

            changes_data = {
                    'instrument': instrument,
                    'start_date': result['start_date'].strftime('%Y-%m-%d'),
                    'end_date': result['end_date'].strftime('%Y-%m-%d'),
                    'total_change': Query.get_total_change(result['start_date'], result['end_date'], instrument),
            }
            gaines.append(changes_data)
        gaines = [g for g in gaines if g['total_change']<0]
        sorted_gains = sorted(gaines, key=lambda x: x['total_change'])
        print(sorted_gains)
        return sorted_gains
    def resolve_instruments(self, info):
        instruments = StockData.objects.values("instrument").distinct()
        instrument_names = [item["instrument"] for item in instruments]
        return list(set(instrument_names))
