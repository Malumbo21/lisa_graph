from django.contrib import admin
from .models import StockDataV2

class StockDataV2Admin(admin.ModelAdmin):
	list_display = '__all__'
	list_filter = ('instrument',)
	search_fields = ('instrument',)

admin.site.register(StockDataV2, StockDataV2Admin)