import graphene
from datetime import datetime
from stock_data.models import StockDataV2
from django.db import models
from django.db.models.functions import Cast
from django.db.models import F, Value
from graphene_django import DjangoObjectType

class StockDataV2Type(DjangoObjectType):

	class Meta:
		model = StockDataV2
class Query(graphene.ObjectType):
	stock_data = graphene.List(StockDataV2Type, start=graphene.String(), end=graphene.String(), symbol=graphene.String(), single_date=graphene.Boolean(), date=graphene.String())
	top_movers = graphene.List(StockDataV2Type, n=graphene.Int(), net=graphene.Boolean())
	top_losers = graphene.List(StockDataV2Type, n=graphene.Int(), net=graphene.Boolean())
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

	def resolve_top_movers(self, info, n=None, net=False):
		if net:
			data = StockDataV2.objects.order_by('-net_change')
		else:
			data = StockDataV2.objects.order_by('-change')

		if n is not None:
			return data[:n]
		else:
			return data[:5]
	def resolve_top_losers(self, info, n=None, net=False):
		if net:
			data = StockDataV2.objects.order_by('net_change')
		else:
			data = StockDataV2.objects.order_by('change')
		if n is not None:
			return data[:n]
		else:
			return data[:5]
