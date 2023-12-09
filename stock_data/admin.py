from django.contrib import admin
from .models import StockData

class StockDataAdmin(admin.ModelAdmin):
	list_display = '__all__'
	list_filter = ('instrument',)
	search_fields = ('instrument',)