from django.db import models

class StockDataV2(models.Model):
	instrument = models.CharField(max_length=255, db_index=True)
	bid_qty = models.IntegerField()
	bid_price = models.FloatField()
	ask_price = models.FloatField()
	ask_qty = models.IntegerField()
	last_trade_price = models.FloatField()
	net_change = models.FloatField()
	closing_price = models.FloatField()
	total_turnover = models.FloatField()
	average_price = models.FloatField()
	last_traded_size = models.IntegerField()
	week_52_high = models.FloatField()
	week_52_low = models.FloatField()
	opening_price = models.FloatField()
	change = models.FloatField()
	total_trades = models.IntegerField()
	trade_volume = models.IntegerField()
	foreign_buys = models.IntegerField()
	foreign_sells = models.IntegerField()
	date = models.DateField()

	class Meta:
		db_table = 'stock_data_v2'
		ordering = ('-date',)
