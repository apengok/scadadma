# -*- coding:utf-8 -*-

from django.contrib import admin
from . models import DMABaseinfo,DmaStation,DmaGisinfo
# Register your models here.
from legacy.models import Bigmeter,District
from entm.models import Organization
from django.conf.urls import url
from django.shortcuts import render,redirect
from entm.forms import CsvImportForm
import unicodecsv

@admin.register(DmaStation)
class DmaStationAdmin(admin.ModelAdmin):
    list_display = ['dmaid','station_id','meter_type','station_type']

    change_list_template = "entm/heroes_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            # ...
            url('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            reader = unicodecsv.reader(csv_file)
            # Create Hero objects from passed in data
            # ...
            headers = next(reader)
            print(headers,len(headers))
            # data = {i: v for (i, v) in enumerate(reader)}
            # organ = Organization.objects.first()
            for row in reader:
                # print(row,len(row))
                data = {headers[i]:v for (i, v) in enumerate(row)}
                del data["id"]
                print(data)
                dmaid = data["dmaid"]
                try:
                    dmaid_f = DMABaseinfo.objects.get(dma_name=dmaid)
                except:
                    print("the dma not exist.")
                    dmaid_f = DMABaseinfo.objects.first()
                data["dmaid"] = dmaid_f
                
                DmaStation.objects.create(**data)
                # for i in range(len(row)):
                #     print("{}.{}={}".format(i,headers[i],row[i]))
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "entm/csv_form.html", payload
        )


@admin.register(DMABaseinfo)
class DMABaseinfoAdmin(admin.ModelAdmin):
    list_display = ['dma_no','dma_level','dma_name','creator','create_date','belongto']
    search_fields = ("dma_no","dma_name" )

    change_list_template = "entm/heroes_changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            # ...
            url('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            reader = unicodecsv.reader(csv_file)
            # Create Hero objects from passed in data
            # ...
            headers = next(reader)
            print(headers,len(headers))
            # data = {i: v for (i, v) in enumerate(reader)}
            
            for row in reader:
                # print(row,len(row))
                data = {headers[i]:v for (i, v) in enumerate(row)}
                del data["id"]
                parent_name = data["belongto"]
                try:
                    organ = Organization.objects.get(name=parent_name)
                except:
                    organ = Organization.objects.first()
                data["belongto"] = organ
                # data = ["{}={}".format(headers[i],v) for (i, v) in enumerate(row)]
                # tdata = list("{}={}".format(k,v) for k,v in data.items())
                print(data)
                
                DMABaseinfo.objects.create(**data)
                # for i in range(len(row)):
                #     print("{}.{}={}".format(i,headers[i],row[i]))
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "entm/csv_form.html", payload
        )


@admin.register(DmaGisinfo)
class DmaGisInfoAdmin(admin.ModelAdmin):
    list_display = ['dma_no','geodata','strokeColor','fillColor']
