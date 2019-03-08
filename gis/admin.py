# -*- coding:utf-8 -*-

from django.contrib import admin
from . import models
from entm.models import Organization
from django.conf.urls import url
from django.shortcuts import render,redirect
from entm.forms import CsvImportForm
import unicodecsv

# Register your models here.

@admin.register(models.FenceDistrict)
class FenceDistrictAdmin(admin.ModelAdmin):
    list_display = ['name','parent','belongto','ftype','createDataTime','createDataUsername','cid','pId','updateDataTime','updateDataUsername']

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
                del data["lft"]
                del data["rght"]
                del data["tree_id"]
                del data["level"]
                del data["parent"]
                print(data)
                
                parent_name = data["belongto"]
                try:
                    organ = Organization.objects.get(name=parent_name)
                except:
                    organ = Organization.objects.first()
                data["belongto"] = organ

                models.FenceDistrict.objects.create(**data)
                # for i in range(len(row)):
                #     print("{}.{}={}".format(i,headers[i],row[i]))
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "entm/csv_form.html", payload
        )

@admin.register(models.FenceShape)
class FenceShapeAdmin(admin.ModelAdmin):
    list_display = ['shapeId','name','zonetype','shape','dma_no','pointSeqs','longitudes','latitudes','lnglatQuery_LU','lnglatQuery_RD']

    fieldsets = (
        (None, {'fields': ('shapeId', 'name','zonetype','shape','dma_no','strokeColor','fillColor')}),
        ('Polygon', {'fields': ('pointSeqs','longitudes','latitudes')}),
        ('Rectangle', {'fields': ('lnglatQuery_LU','lnglatQuery_RD')}),
        ('Circle', {'fields': ('centerPointLat','centerPointLng','centerRadius')}),
        ('Administrator', {'fields': ('province','city','district','administrativeLngLat')}),
    )

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
                # print(data)
                
                models.FenceShape.objects.create(**data)
                # for i in range(len(row)):
                #     print("{}.{}={}".format(i,headers[i],row[i]))
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "entm/csv_form.html", payload
        )    