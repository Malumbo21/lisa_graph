import graphene
from datetime import datetime, timedelta
from stock_data.models import StockDataV2
from django.db import models
from django.db.models.functions import Cast, Lag
from django.db.models import F, Value, Max, Q, ExpressionWrapper, fields, Window
from graphene_django import DjangoObjectType

class StockDataV2Type(DjangoObjectType):
    class Meta:
        model = StockDataV2

class Query(graphene.ObjectType):
    stock_data = graphene.List(StockDataV2Type, start=graphene.String(), end=graphene.String(), symbol=graphene.String(), single_date=graphene.Boolean(), date=graphene.String())
    instruments = graphene.List(graphene.String)
    top_gainers = graphene.List(StockDataV2Type, n=graphene.Int(), day=graphene.Boolean(), week=graphene.Boolean(), month=graphene.Boolean(), year=graphene.Boolean(), date=graphene.String())
    top_losers = graphene.List(StockDataV2Type, n=graphene.Int(), day=graphene.Boolean(), week=graphene.Boolean(), month=graphene.Boolean(), year=graphene.Boolean())
    weekly_high_low = graphene.List(
        StockDataV2Type,
        instrument=graphene.String(),
        year=graphene.Int(),
        month=graphene.Int(),
        n=graphene.Int()
    )

    def resolve_weekly_high_low(self, info, instrument=None, year=None, month=None, n=None):
        # Filtering based on the given instrument, year, and month
        data = StockDataV2.objects.all()
        if instrument:
            data = data.filter(instrument=instrument)
        if year:
            data = data.filter(date__year=year)
        if month:
            data = data.filter(date__month=month)

        # Calculate the start of the week dynamically
        window = Window(partition_by='instrument', order_by=F('date').asc())
        data = data.annotate(
            week_start=ExpressionWrapper(
                F('date') - ExtractWeek(F('date')) * Value(timedelta(days=1)),
                output_field=fields.DateField()
            )
        )

        # Calculate the price difference for each week
        data = data.annotate(
            price_diff=ExpressionWrapper(
                F('closing_price') - Lag('closing_price', default=Value(F('closing_price'))).over(window),
                output_field=fields.DecimalField()
            )
        )

        # Get the weekly high and low
        weekly_high_low_data = []
        if n is not None:
            # Get the top N weekly differences
            data = data.order_by('-price_diff')[:n]

        # Group data by week_start and get the first and last records for each week
        grouped_data = data.order_by('week_start').values('week_start').annotate(
            first_record=Min('date'),
            last_record=Max('date'),
            weekly_high=Max('closing_price'),
            weekly_low=Max('closing_price'),
        )

        for record in grouped_data:
            weekly_high_low_data.append({
                'week_start': record['week_start'],
                'first_record': record['first_record'],
                'last_record': record['last_record'],
                'weekly_high': record['weekly_high'],
                'weekly_low': record['weekly_low'],
            })

        return weekly_high_low_data
    def resolve_stock_data(self, info, start=None, end=None, symbol=None, single_date=False, date=None):
        data = StockDataV2.objects.all()
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
                data = data.filter(date_range=(start, end))
        if end:
            if start is None:
                endtime = datetime.strptime(end, "%Y-%m-%d").date()
                data = data.filter(date__lte=endtime)
        return data

    def resolve_top_gainers(self, info, n=None, day=False, week=False, month=False, year=False, date=None):
        if not any([day, week, month, year]):
            raise Exception("Error: Set at least one of the timeframe options (day, week, month, year) to True")

        date = StockDataV2.objects.aggregate(Max('date'))['date__max']

        if day:
            data = StockDataV2.objects.filter(date=date)
        elif week:
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            data = StockDataV2.objects.filter(date__range=[start_of_week, end_of_week])
        elif month:
            data = StockDataV2.objects.filter(date__month=date.month, date__year=date.year)
        elif year:
            data = StockDataV2.objects.filter(date__year=date.year)

        window = Window(partition_by='instrument', order_by=F('date').desc())
        data = data.annotate(
            price_diff=ExpressionWrapper(
                F('closing_price') - Lag('closing_price', default=Value(F('closing_price'))).over(window),
                output_field=fields.DecimalField()
            )
        )

        if n is not None:
            return data.order_by('-price_diff')[:n]
        else:
            return data.order_by('-price_diff')[:5]

    def resolve_top_losers(self, info, n=None, day=False, week=False, month=False, year=False):
        if not any([day, week, month, year]):
            raise Exception("Error: Set at least one of the timeframe options (day, week, month, year) to True")

        date = StockDataV2.objects.aggregate(Max('date'))['date__max']

        if day:
            data = StockDataV2.objects.filter(date=date)
        elif week:
            start_of_week = date - timedelta(days=date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            data = StockDataV2.objects.filter(date__range=[start_of_week, end_of_week])
        elif month:
            data = StockDataV2.objects.filter(date__month=date.month, date__year=date.year)
        elif year:
            data = StockDataV2.objects.filter(date__year=date.year)

        data = data.annotate(
            price_diff=ExpressionWrapper(
                F('closing_price') - Lag('closing_price', default=Value(F('closing_price')), partition_by=F('instrument')).over(order_by=F('-date')),
                output_field=fields.DecimalField()
            )
        )

        if n is not None:
            return data.order_by('price_diff')[:n]
        else:
            return data.order_by('price_diff')[:5]

    def resolve_instruments(self, info):
        instruments = StockDataV2.objects.values("instrument").distinct()

        instrument_names = [item["instrument"] for item in instruments]

        return list(set(instrument_names))
