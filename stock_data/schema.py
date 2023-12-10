import graphene
from datetime import datetime
from stock_data.models import StockData
from django.db import models
from django.db.models.functions import Cast
from django.db.models import F, Value
from graphene_django import DjangoObjectType

class StockDataType(DjangoObjectType):

	class Meta:
		model = StockData
	date = graphene.String()
	bid_qty = graphene.String()
    ask_qty = graphene.String()
    last_traded_size = graphene.String()
    total_trades = graphene.String()
    trade_volume = graphene.String()
    foreign_buys = graphene.String()
    foreign_sells = graphene.String()

    # Include the remaining fields
class Query(graphene.ObjectType):
	stock_data = graphene.List(StockDataType, start=graphene.String(), end=graphene.String(), symbol=graphene.String(), single_date=graphene.Boolean(), date=graphene.String())
	def resolve_stock_data(self, info, start=None, end=None, symbol=None, single_date=False, date=None):
		data = StockData.objects.all()
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
