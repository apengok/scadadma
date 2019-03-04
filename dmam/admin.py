# -*- coding:utf-8 -*-

from django.contrib import admin
from . models import DMABaseinfo,DmaStation,DmaGisinfo
# Register your models here.
from legacy.models import Bigmeter,District


@admin.register(DmaStation)
class DmaStationAdmin(admin.ModelAdmin):
    list_display = ['dmaid','station_id','meter_type','station_type']


@admin.register(DMABaseinfo)
class DMABaseinfoAdmin(admin.ModelAdmin):
    list_display = ['dma_no','dma_level','dma_name','creator','create_date','belongto']
    search_fields = ("dma_no","dma_name" )


@admin.register(DmaGisinfo)
class DmaGisInfoAdmin(admin.ModelAdmin):
    list_display = ['dma_no','geodata','strokeColor','fillColor']
