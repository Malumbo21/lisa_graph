from django.test import TestCase
from config.schema import schema
from stock_data.models import StockData

class StockDataTest(TestCase):

	def test_get_all_data(self):
		len_all_data = len(StockData.objects.all())
		query = '''
					{
					stockData {
					id
					}
					}
				'''
		result = schema.execute(query)
		assert not result.errors
		print(len(result.data))
		print(result.data)
		assert len_all_data == len(result.data)