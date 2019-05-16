# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404,render,redirect
from django.http import HttpResponse,JsonResponse,HttpResponseRedirect,StreamingHttpResponse
from django.contrib import messages
from django.template import TemplateDoesNotExist
import json
import random
import datetime
import time

from mptt.utils import get_cached_trees
from mptt.templatetags.mptt_tags import cache_tree_children
from django.contrib.auth.mixins import PermissionRequiredMixin,UserPassesTestMixin
from django.template.loader import render_to_string
from django.shortcuts import render,HttpResponse
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView,DeleteView,FormView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import admin
from django.contrib.auth.models import Permission
from django.utils.safestring import mark_safe
from django.utils.encoding import escape_uri_path
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from collections import OrderedDict
from accounts.models import MyUser,MyRoles

from entm.utils import unique_cid_generator,unique_uuid_generator,unique_rid_generator

from entm.models import Organization
from legacy.models import Bigmeter,District,Community,HdbFlowData,HdbFlowDataDay,HdbFlowDataMonth,HdbPressureData,Watermeter
from . models import DMABaseinfo,DmaStation,DmaGisinfo

from . forms import DMACreateForm,DMABaseinfoForm,StationAssignForm
import os
from django.conf import settings
from .utils import merge_values,merge_values_to_dict
from scadadma.mixins import AjaxableResponseMixin
from django.core.files.storage import FileSystemStorage

import logging

logger_info = logging.getLogger('info_logger')
logger_error = logging.getLogger('error_logger')


# dmaam


def dmatree(request):   
    organtree = []
    
    stationflag = request.POST.get("isStation") or ''
    dmaflag = request.POST.get("isDma") or ''
    districtflag = request.POST.get("isDistrict") or ''
    communityflag = request.POST.get("isCommunity") or ''
    buidlingflag = request.POST.get("isBuilding") or ''
    pressureflag = request.POST.get("isPressure") or ''
    protocolflag = request.POST.get("isProtocol") or ''
    secondwaterflag = request.POST.get("isSecondwater") or ''
    user = request.user
    
    # if user.is_anonymous:
    if not user.is_authenticated:
        organs = Organization.objects.first()
    else:
        organs = user.belongto #Organization.objects.all()
        if organs is None:
            organs = Organization.objects.filter(name='歙县')[0]
    
    # 组织
    if dmaflag == "1":
        organ_lists = organs.get_descendants(include_self=True).values("id","name","cid","pId","uuid","organlevel","attribute")
    else:
        organ_lists = Organization.objects.filter(name='歙县').values("id","name","cid","pId","uuid","organlevel","attribute")
        shexian_organ_cid = organ_lists[0]["cid"]
    # print(organ_lists)

    #district
    district_lists = District.objects.values("id","name")
    
    # mergeds = merge_values(o_lists)
    #dma
    dma_lists = DMABaseinfo.objects.values("pk","dma_name","dma_no","belongto__cid","belongto__organlevel")
    # merged_dma = merge_values_to_dict(dma_lists,"belongto__cid")
    #station
    station_lists = Bigmeter.objects.values("pk","username","commaddr","districtid")
    #community
    comunity_lists = Community.objects.values("id","name","districtid")
    #pressure
    # pressure_lists = user.pressure_list_queryset('').values("pk","username","simid__simcardNumber","belongto__cid")

    p_dma_no='' #dma_lists[0]['dma_no'] 
    
    for o in organ_lists:
        organtree.append({
            "name":o["name"],
            "id":o["cid"],
            "pId":o["pId"],
            "attribute":o["attribute"],
            "organlevel":o["organlevel"],
            "districtid":'',
            "type":"group",
            # "dma_no":o["dma__dma_no"] if o["dma__dma_no"] else '',  #如果存在dma分区，分配第一个dma分区的dma_no，点击数条目的时候使用
            "icon":"/static/virvo/resources/img/wenjianjia.png",
            "uuid":o["uuid"]
        })   
    
    #dma
    if dmaflag == '1':
        for d in dma_lists:
            organtree.append({
                "name":d["dma_name"],
                "id":d["pk"],
                "districtid":d["pk"],
                "pId":d["belongto__cid"],
                "type":"dma",
                "dma_no":d["dma_no"],
                "leakrate":random.choice([9.65,13.46,11.34,24.56,32.38,7.86,10.45,17.89,23.45,36,78]),
                "dmalevel":d["belongto__organlevel"],
                "icon":"/static/virvo/resources/img/dma.png",
                "uuid":''
            })
            
    #歙县district
    if districtflag == '1':
        for d in district_lists:
            # print("id_{}_name{}--pId:{}".format(d["id"],d["name"],shexian_organ_cid))
            organtree.append({
                "name":d["name"],
                "id":"district_{}".format(d["id"]),
                "districtid":d["id"],
                "pId":shexian_organ_cid,
                "type":"district",
                "dma_no":"",
                "leakrate":random.choice([9.65,13.46,11.34,24.56,32.38,7.86,10.45,17.89,23.45,36,78]),
                "dmalevel":"",
                "icon":"/static/virvo/resources/img/wenjianjia.png",
                "uuid":''
            })
            
            

        #station
        # 会出现pk 和 username list长度不等的情况，可能有同名站点
    if stationflag == '1':
        for s in station_lists:
            organtree.append({
                        "name":s['username'],
                        "id":s['pk'],
                        "districtid":s['districtid'],
                        "pId":"district_{}".format(s["districtid"]) if districtflag == "1" else shexian_organ_cid,
                        "type":"station",
                        "dma_no":'',

                        "commaddr":s["commaddr"],
                        "dma_station_type":"1", # 在dma站点分配中标识该是站点还是小区
                        "icon":"/static/virvo/resources/img/station.png",
                        "uuid":''
                    })
        

    
    #community
    if communityflag == '1':
        for c in comunity_lists:
            # print("\tid_{}_name{}--pId:{}".format(c["id"],c["name"],c["districtid"]))

            community_name = c['name']
            # 小区列表
            organtree.append({
                "name":c['name'],
                "id":c['id'],
                "districtid":c["districtid"],
                "pId":"district_{}".format(c["districtid"]) ,
                "type":"community",
                "dma_no":'',
                "open":False,
                "commaddr":c['id'],#在dma站点分配中需要加入小区的分配，在这里传入小区的id，在后续处理中通过小区id查找小区及对应的集中器等
                "dma_station_type":"2", # 在dma站点分配中标识该是站点还是小区
                "icon":"/static/virvo/resources/img/home.png",
                "uuid":''
            })

            

        
    # for o in organ_lists:
    #     organtree.append({
    #         "name":o["name"],
    #         "id":o["cid"],
    #         "pId":o["pId"],
    #         "attribute":o["attribute"],
    #         "organlevel":o["organlevel"],
    #         "districtid":'',
    #         "type":"group",
    #         # "dma_no":o["dma__dma_no"] if o["dma__dma_no"] else '',  #如果存在dma分区，分配第一个dma分区的dma_no，点击数条目的时候使用
    #         "icon":"/static/virvo/resources/img/wenjianjia.png",
    #         "uuid":o["uuid"]
    #     })   
    
    
    result = dict()
    result["data"] = organtree
    
    # print(json.dumps(result))
    # print(result)
    
    return HttpResponse(json.dumps(organtree))




def getDmaSelect(request):
    print("getDmaSelect.....")
    dmas = DMABaseinfo.objects.values("dma_no","dma_name")

    def m_info(m):
        
        return {
            "dma_no":m["dma_no"],
            "dma_name":m["dma_name"],
            
        }
    data = []

    for m in dmas:
        data.append(m_info(m))

    operarions_list = {
        "exceptionDetailMsg":"null",
        "msg":None,
        "obj":data,
        "success":True
    }
   
    # print(operarions_list)
    return JsonResponse(operarions_list)

def getmeterlist(request):

    meters = Meter.objects.all()

    def m_info(m):
        
        return {
            "id":m.pk,
            "serialnumber":m.serialnumber,
            
        }
    data = []

    for m in meters:
        data.append(m_info(m))

    operarions_list = {
        "exceptionDetailMsg":"null",
        "msg":None,
        "obj":{
                "meterlist":data
        },
        "success":True
    }
   

    return JsonResponse(operarions_list)


def getmeterParam(request):

    mid = request.POST.get("mid")
    meter = Meter.objects.get(id=int(mid))
    operarions_list = {
        "exceptionDetailMsg":"null",
        "msg":None,
        "obj":{
                "id":meter.pk,
                "simid":meter.simid.simcardNumber if meter.simid else "",
                "dn":meter.dn,
                "belongto":meter.belongto.name,#current_user.belongto.name,
                "metertype":meter.metertype,
                "serialnumber":meter.serialnumber,
        },
        "success":True
    }
   

    return JsonResponse(operarions_list)

# dma管理-站点管理页面站点列表
def stationlist(request):
    draw = 1
    length = 0
    start=0
    t1 = time.time()
    if request.method == "GET":
        draw = int(request.GET.get("draw", 1))
        length = int(request.GET.get("length", 10))
        start = int(request.GET.get("start", 0))
        search_value = request.GET.get("search[value]", None)
        # order_column = request.GET.get("order[0][column]", None)[0]
        # order = request.GET.get("order[0][dir]", None)[0]
        groupName = request.GET.get("groupName")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print("simpleQueryParam",simpleQueryParam)

    if request.method == "POST":
        draw = int(request.POST.get("draw", 1))
        length = int(request.POST.get("length", 10))
        start = int(request.POST.get("start", 0))
        pageSize = int(request.POST.get("pageSize", 10))
        search_value = request.POST.get("search[value]", None)
        # order_column = request.POST.get("order[0][column]", None)[0]
        # order = request.POST.get("order[0][dir]", None)[0]
        groupName = request.POST.get("groupName")   #selected treeid
        districtId = request.POST.get("districtId")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print(request.POST.get("draw"))
        print("groupName",groupName)
        print("districtId:",districtId)
        # print("post simpleQueryParam",simpleQueryParam)

    

    #当前登录用户
    current_user = request.user

    
    data = []
    
    stations = current_user.station_list_queryset(simpleQueryParam)

    if districtId != '': #dma
        dma = DMABaseinfo.objects.get(pk=int(districtId))
        dma_stations = dma.station_set.all()
        # stations = [s for s in dma_stations if s in stations]
    elif groupName != '':
        filter_group = Organization.objects.get(cid=groupName)
        filter_group_name = filter_group.name
        # stations = [s for s in stations if s.belongto == filter_group]
    
    def u_info(u):  #u means station

        return {
            "id":u["id"],
            "username":u["username"],
            "usertype":u["usertype"],
            "simid":u["meter__simid__simcardNumber"],
            "dn":u["meter__dn"],
            "belongto":u["belongto__name"],# if u.meter else '',#current_user.belongto.name,
            "metertype":u["meter__metertype"],
            "serialnumber":u["meter__serialnumber"],
            "big_user":u["biguser"],
            "focus":u["focus"],
            "createdate":u["madedate"],
            "related":DmaStation.objects.filter(station_id=u["meter__simid__simcardNumber"]).exists()
            # "related":False if u["dmaid__dma_no"] is None else True
        }

    for m in stations.values("id","username","usertype","meter__dn","biguser","focus",
                    "meter__metertype","meter__serialnumber","meter__simid__simcardNumber","madedate","belongto__name","dmaid__dma_no"):
        if groupName != "":
            if filter_group_name != m["belongto__name"]:
                continue
        data.append(u_info(m))
    
    recordsTotal = len(stations)
    # recordsTotal = len(data)
    
    result = dict()
    result["records"] = data[start:start+length]
    result["draw"] = draw
    result["success"] = "true"
    result["pageSize"] = pageSize
    result["totalPages"] = recordsTotal/pageSize
    result["recordsTotal"] = recordsTotal
    result["recordsFiltered"] = recordsTotal
    result["start"] = 0
    result["end"] = 0

    
    print("dma station time last ",time.time()-t1)
    return HttpResponse(json.dumps(result))


def dmastationlist(request):
    print("dmastationlist where are from?",request.POST,request.kwargs)
    draw = 1
    length = 0
    start=0
    
    if request.method == "GET":
        draw = int(request.GET.get("draw", 1))
        length = int(request.GET.get("length", 10))
        start = int(request.GET.get("start", 0))
        search_value = request.GET.get("search[value]", None)
        # order_column = request.GET.get("order[0][column]", None)[0]
        # order = request.GET.get("order[0][dir]", None)[0]
        groupName = request.GET.get("groupName")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print("simpleQueryParam",simpleQueryParam)

    if request.method == "POST":
        draw = int(request.POST.get("draw", 1))
        length = int(request.POST.get("length", 10))
        start = int(request.POST.get("start", 0))
        pageSize = int(request.POST.get("pageSize", 10))
        search_value = request.POST.get("search[value]", None)
        # order_column = request.POST.get("order[0][column]", None)[0]
        # order = request.POST.get("order[0][dir]", None)[0]
        groupName = request.POST.get("groupName")
        districtId = request.POST.get("districtId")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print(request.POST.get("draw"))
        print("groupName",groupName)
        print("districtId:",districtId)
        # print("post simpleQueryParam",simpleQueryParam)

    

    #当前登录用户
    current_user = request.user

    def u_info(u):
        
        return {
            "id":u.pk,
            "username":u.username,
            "usertype":u.usertype,
            "simid":u.meter.simid.simcardNumber if u.meter and u.meter.simid else '',
            "dn":u.meter.dn if u.meter else '',
            "belongto":u.meter.belongto.name if u.meter else '',#current_user.belongto.name,
            "metertype":u.meter.metertype if u.meter else '',
            "serialnumber":u.meter.serialnumber if u.meter else '',
            "big_user":1,
            "focus":1,
            "createdate":u.madedate
        }
    data = []
    
    
    # userl = current_user.user_list()

    # bigmeters = Bigmeter.objects.all()
    # dma_pk = request.POST.get("pk") or 4
    dma_pk=4
    dma = DMABaseinfo.objects.first() #get(pk=int(dma_pk))
    stations = dma.station_set_all() # dma.station_set.all()
    
    
    

    

    for m in stations[start:start+length]:
        data.append(u_info(m))
    
    recordsTotal = len(stations)
    # recordsTotal = len(data)
    
    result = dict()
    result["records"] = data
    result["draw"] = draw
    result["success"] = "true"
    result["pageSize"] = pageSize
    result["totalPages"] = recordsTotal/pageSize
    result["recordsTotal"] = recordsTotal
    result["recordsFiltered"] = recordsTotal
    result["start"] = 0
    result["end"] = 0

    
    
    return HttpResponse(json.dumps(result))

# class DistrictFormView(FormView):
#     form_class = DMABaseinfoForm
# DMA管理基础页面
def dmabaseinfo(request):
    t1 = time.time()
    if request.method == 'GET':
        
        data = []
        dma_no = request.GET.get("dma_no")
        if dma_no == '':
            operarions_list = {
                "exceptionDetailMsg":"null",
                "msg":None,
                "obj":{
                        "baseinfo":{
                            "dma_no":'',
                            "pepoles_num":'',
                            "acreage":'',
                            "user_num":'',
                            "pipe_texture":'',
                            "pipe_length":'',
                            "pipe_links":'',
                            "pipe_years":'',
                            "pipe_private":'',
                            "ifc":'',
                            "aznp":'',
                            "night_use":'',
                            "cxc_value":'',
                            "belongto":''
                            },
                        "dmastationlist":data
                },
                "success":True
            }
           

            return JsonResponse(operarions_list)
            

        # dmabase = DMABaseinfo.objects.get(dma_no=dma_no)

        
        def assigned(a):
            commaddr = a["station_id"]     # 大表 通讯地址commaddr 或者 小区关联的集中器pk(or id)，由station_type 标识
            
            station_type = a["station_type"] # 大表还是小区 1-大表 2-小区
            if station_type == '1':
                s = Bigmeter.objects.filter(commaddr=commaddr).values("pk","username","usertype","dn",
                    "metertype","serialnumber","madedate","districtid")[0]
                edit_id = s["pk"]
                username = s["username"]
                usertype = s["usertype"]
                simid =commaddr
                dn = s["dn"]
                belongto_name = s["districtid"]
                metertype = s["metertype"]
                serialnumber = s["serialnumber"]
                createdate = s["madedate"]
            elif station_type == '2':
                # s = VCommunity.objects.filter(id=commaddr).values("id","name","vconcentrators__name","districtid")[0]
                s = Community.objects.filter(id=commaddr).values("id","name","districtid")[0]
                edit_id = s["id"]
                username = s["name"]
                usertype = "小区"
                simid =commaddr
                dn = ""
                belongto_name = s["districtid"]
                metertype = "小区"
                serialnumber = ""
                createdate = ""
        
            return {
                "id":edit_id,
                "username":username,
                "usertype":usertype,
                "simid":simid, #u.meter.simid.simcardNumber if u.meter and u.meter.simid else '',
                "dn":dn, #u.meter.dn if u.meter else '',
                "belongto":belongto_name, # u.meter.belongto.name if u.meter else '',#current_user.belongto.name,
                "metertype":metertype, #u.meter.metertype if u.meter else '',
                "serialnumber":serialnumber, # u.meter.serialnumber if u.meter else '',
                "big_user":1,
                "focus":1,
                "createdate":createdate, #u.madedate
            }
        
        #dma分区的站点
        # stations = dmabase.station_set.all()
        # for s in stations:
        #     data.append(u_info(s))
        # 从DmaStation获取dma分配的站点
        dmabase = DMABaseinfo.objects.get(dma_no=dma_no)
        belongto_name = dmabase.belongto.name
        stations = dmabase.station_assigned().values()
        for s in stations:
            data.append(assigned(s))

        dmabase = DMABaseinfo.objects.filter(dma_no=dma_no).values()[0]
        operarions_list = {
            "exceptionDetailMsg":"null",
            "msg":None,
            "obj":{
                    "baseinfo":{
                        "dma_no":dmabase["dma_no"],
                        "pepoles_num":dmabase["pepoles_num"],
                        "acreage":dmabase["acreage"],
                        "user_num":dmabase["user_num"],
                        "pipe_texture":dmabase["pipe_texture"],
                        "pipe_length":dmabase["pipe_length"],
                        "pipe_links":dmabase["pipe_links"],
                        "pipe_years":dmabase["pipe_years"],
                        "pipe_private":dmabase["pipe_private"],
                        "ifc":dmabase["ifc"],
                        "aznp":dmabase["aznp"],
                        "night_use":dmabase["night_use"],
                        "cxc_value":dmabase["cxc_value"],
                        "belongto":belongto_name
                        },
                    "dmastationlist":data
            },
            "success":True
        }
       
        print("dmabase time last ",time.time()-t1)
        return JsonResponse(operarions_list)

    if request.method == 'POST':
        print('dmabaseinfo post:',request.POST)
        # dma_no = request.POST.get("dma_no")
        # dmabase = DMABaseinfo.objects.get(dma_no=dma_no)
        # form = DMABaseinfoForm(request.POST or None)
        # if form.is_valid():
        #     form.save()
        #     flag = 1
        # err_str = ""
        # if form.errors:
        #     flag = 0
        #     for k,v in form.errors.items():
        #         print(k,v)
        #         err_str += v[0]
    
        # data = {
        #     "success": flag,
        #     "errMsg":err_str
            
        # }
        
        # return HttpResponse(json.dumps(data)) #JsonResponse(data)


    return HttpResponse(json.dumps({"success":True}))


def getdmamapusedata(request):
    print('getdmamapusedata:',request.GET)
    dma_name = request.GET.get("dma_name")
    dma = DMABaseinfo.objects.get(dma_name=dma_name)
    dmastation = dma.dmastation.first()
    commaddr = dmastation.station_id

    dmaflow = 0
    month_sale = 0
    lastmonth_sale = 0
    bili = 0
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_flow = HdbFlowDataDay.objects.filter(hdate=today_str)
    if today_flow.exists():
        dmaflow = today_flow.first().dosage

    month_str = today.strftime("%Y-%m")
    month_flow = HdbFlowDataMonth.objects.filter(hdate=month_str)
    if month_flow.exists():
        month_sale = month_flow.first().dosage

    lastmonth = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
    lastmonth_str = lastmonth.strftime("%Y-%m")
    lastmonth_flow = HdbFlowDataMonth.objects.filter(hdate=lastmonth_str)
    if lastmonth_flow.exists():
        lastmonth_sale = lastmonth_flow.first().dosage

    if float(month_sale) > 0 and float(lastmonth_sale) > 0:
        bili =  (float(month_sale) - float(lastmonth_sale) ) / float(lastmonth_sale)

    data = {
        "dma_statics":{
            "belongto":dma.belongto.name,
            "dma_level":"二级",
            "dma_status":"在线",
            "dmaflow":round(float(dmaflow),2),
            "month_sale":round(float(month_sale),2),
            "lastmonth_sale":round(float(lastmonth_sale),2),
            "bili":round(bili,2)
        }
    }

    return HttpResponse(json.dumps(data))

class DMABaseinfoEditView(AjaxableResponseMixin,UpdateView):
    model = DMABaseinfo
    form_class = DMABaseinfoForm
    template_name = "dmam/baseinfo.html"
    success_url = reverse_lazy("dmam:districtmanager");

    # @method_decorator(permission_required("dma.change_stations"))
    def dispatch(self, *args, **kwargs):
        # self.role_id = kwargs["pk"]
        return super(DMABaseinfoEditView, self).dispatch(*args, **kwargs)

    def test_func(self):
        if self.request.user.has_menu_permission_edit('districtmanager_dmam'):
            return True
        return False

    def handle_no_permission(self):
        data = {
                "mheader": "修改用户",
                "err_msg":"您没有权限进行操作，请联系管理员."
                    
            }
        # return HttpResponse(json.dumps(err_data))
        return render(self.request,"dmam/permission_error.html",data)

    def form_invalid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        print("dmabaseinfo edit form_invalid?:",self.request.POST)
        # print(form)
        # do something
        
                

        return super(DMABaseinfoEditView,self).form_invalid(form)

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        print("dmabaseinfo edit here?:",self.request.POST)
        # print(form)
        # do something
        belongto_name = form.cleaned_data.get("belongto")
        print('belongto_name',belongto_name)
        organ = Organization.objects.get(name=belongto_name)
        instance = form.save(commit=False)
        instance.belongto = organ
                

        return super(DMABaseinfoEditView,self).form_valid(form)

    # def get_object(self):
    #     print(self.kwargs)
    #     return Organization.objects.get(cid=self.kwargs["pId"])

class DistrictMangerView(TemplateView):
    template_name = "dmam/districtlist.html"

    def get_context_data(self, *args, **kwargs):
        context = super(DistrictMangerView, self).get_context_data(*args, **kwargs)
        context["page_menu"] = "dma管理"
        # context["page_submenu"] = "组织和用户管理"
        context["page_title"] = "dma分区管理"
        user_organ = '歙县'   #self.request.user.belongto

        default_dma = DMABaseinfo.objects.first()   # user_organ.dma.all().first()
        print('districtmanager',default_dma.pk,default_dma.dma_name)
        context["current_dma_pk"] = default_dma.pk if default_dma else ''
        context["current_dma_no"] = default_dma.dma_no if default_dma else ''
        context["current_dma_name"] = default_dma.dma_name if default_dma else ''

        # context["user_list"] = User.objects.all()
        

        return context  

    """
group add
"""
def verifydmano(request):
    dma_no = request.POST.get("dma_no")
    bflag = not DMABaseinfo.objects.filter(dma_no=dma_no).exists()

    return HttpResponse(json.dumps({"success":bflag}))

def verifydmaname(request):
    dma_name = request.POST.get("dma_name")
    bflag = not DMABaseinfo.objects.filter(dma_name=dma_name).exists()

    return HttpResponse(json.dumps({"success":bflag}))    


def verifyusername(request):
    username = request.POST.get("username")
    bflag = not Station.objects.filter(username=username).exists()

    return HttpResponse(json.dumps({"success":bflag}))  

class DistrictAddView(AjaxableResponseMixin,CreateView):
    model = Organization
    template_name = "dmam/districtadd.html"
    form_class = DMACreateForm
    success_url = reverse_lazy("dmam:districtmanager");

    # @method_decorator(permission_required("dma.change_stations"))
    def dispatch(self, *args, **kwargs):
        print("dispatch",args,kwargs)
        if self.request.method == "GET":
            cid = self.request.GET.get("id")
            pid = self.request.GET.get("pid")
            kwargs["cid"] = cid
            kwargs["pId"] = pid
        return super(DistrictAddView, self).dispatch(*args, **kwargs)

    def test_func(self):
        if self.request.user.has_menu_permission_edit('districtmanager_dmam'):
            return True
        return False

    def handle_no_permission(self):
        data = {
                "mheader": "修改用户",
                "err_msg":"您没有权限进行操作，请联系管理员."
                    
            }
        # return HttpResponse(json.dumps(err_data))
        return render(self.request,"dmam/permission_error.html",data)

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        print("dma add here?:",self.request.POST)
        print(form)
        # do something
        instance = form.save(commit=False)
        instance.is_org = True
        cid = self.request.POST.get("pId","oranization")  #cid is parent orgnizations
        print('cid:',cid)
        organizaiton_belong = Organization.objects.get(cid=cid)
        instance.belongto = organizaiton_belong
        
        


        return super(DistrictAddView,self).form_valid(form)   

    # def get_context_data(self, *args, **kwargs):
    #     context = super(DistrictAddView, self).get_context_data(*args, **kwargs)
    #     context["cid"] = kwargs.get("cid")
    #     context["pId"] = kwargs.get("pId")
        

    #     return context  

    def get(self,request, *args, **kwargs):
        print("get::::",args,kwargs)
        form = super(DistrictAddView, self).get_form()
        # Set initial values and custom widget
        # initial_base = self.get_initial() #Retrieve initial data for the form. By default, returns a copy of initial.
       
        # initial_base["cid"] = kwargs.get("cid")
        # initial_base["pId"] = kwargs.get("pId")
        # form.initial = initial_base
        cid = kwargs.get("cid")
        pId = kwargs.get("pId")
        
        return render(request,self.template_name,
                      {"form":form,"cid":cid,"pId":pId})


"""
Group edit, manager
"""
class DistrictEditView(AjaxableResponseMixin,UpdateView):
    model = DMABaseinfo
    form_class = DMACreateForm
    template_name = "dmam/districtedit.html"
    success_url = reverse_lazy("dmam:districtmanager");

    # @method_decorator(permission_required("dma.change_stations"))
    def dispatch(self, *args, **kwargs):
        # self.role_id = kwargs["pk"]
        return super(DistrictEditView, self).dispatch(*args, **kwargs)

    def test_func(self):
        if self.request.user.has_menu_permission_edit('districtmanager_dmam'):
            return True
        return False

    def handle_no_permission(self):
        data = {
                "mheader": "修改用户",
                "err_msg":"您没有权限进行操作，请联系管理员."
                    
            }
        # return HttpResponse(json.dumps(err_data))
        return render(self.request,"dmam/permission_error.html",data)

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        print("group update here?:",self.request.POST)
        # print(form)
        # do something
        
                

        return super(DistrictEditView,self).form_valid(form)

    def get_object(self):
        print(self.kwargs)
        return DMABaseinfo.objects.get(pk=self.kwargs["pId"])
        

"""
Group Detail, manager
"""
class DistrictDetailView(DetailView):
    model = DMABaseinfo
    form_class = DMABaseinfoForm
    template_name = "dmam/districtdetail.html"
    # success_url = reverse_lazy("entm:rolemanager");

    # @method_decorator(permission_required("dma.change_stations"))
    def dispatch(self, *args, **kwargs):
        # self.role_id = kwargs["pk"]
        return super(DistrictDetailView, self).dispatch(*args, **kwargs)

    
    def get_object(self):
        print(self.kwargs)
        return DMABaseinfo.objects.get(pk=self.kwargs["pId"])

"""
Assets comment deletion, manager
"""
class DistrictDeleteView(AjaxableResponseMixin,DeleteView):
    model = DMABaseinfo
    # template_name = "aidsbank/asset_comment_confirm_delete.html"

    def dispatch(self, *args, **kwargs):
        # self.comment_id = kwargs["pk"]

        
        print(self.request.POST)
        kwargs["pId"] = self.request.POST.get("pId")
        print("delete dispatch:",args,kwargs)
        return super(DistrictDeleteView, self).dispatch(*args, **kwargs)

    def test_func(self):
        if self.request.user.has_menu_permission_edit('districtmanager_dmam'):
            return True
        return False

    def handle_no_permission(self):
        data = {
                "success": 0,
                "msg":"您没有权限进行操作，请联系管理员."
                    
            }
        return HttpResponse(json.dumps(data))
        # return render(self.request,"dmam/permission_error.html",data)

    def get_object(self,*args, **kwargs):
        print("delete objects:",self.kwargs,kwargs)
        return DMABaseinfo.objects.get(pk=kwargs["pId"])

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.
        """
        print("delete?",args,kwargs)
        self.object = self.get_object(*args,**kwargs)
            

        self.object.delete()
        return JsonResponse({"success":True})


class DistrictAssignStationView(AjaxableResponseMixin,UpdateView):
    model = DMABaseinfo
    form_class = StationAssignForm
    template_name = "dmam/districtassignstation.html"
    success_url = reverse_lazy("dmam:districtmanager");

    # @method_decorator(permission_required("dma.change_stations"))
    def dispatch(self, *args, **kwargs):
        print("dispatch",args,kwargs)
        return super(DistrictAssignStationView, self).dispatch(*args, **kwargs)

    def test_func(self):
        if self.request.user.has_menu_permission_edit('districtmanager_dmam'):
            return True
        return False

    def handle_no_permission(self):
        data = {
                "mheader": "修改用户",
                "err_msg":"您没有权限进行操作，请联系管理员."
                    
            }
        # return HttpResponse(json.dumps(err_data))
        return render(self.request,"dmam/permission_error.html",data)

    def form_valid(self, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        print("dma station assign here?:",self.request.POST)
        # print(form)
        # do something
        stationassign = form.cleaned_data.get("stationassign")
        jd = json.loads(stationassign)

        print(jd)
        self.object = self.get_object()
        for d in jd:
            print(d["station_id"],d["dma_name"],d["station_name"],d["metertype"])
            station_id = int(d["station_id"])
            metertype = d["metertype"]
            station = Station.objects.get(pk=station_id)
            station.dmaid = self.object
            station.dmametertype = metertype
            station.save()
        
        data = {
                "success": 1,
                "obj":{"flag":1}
            }
        return HttpResponse(json.dumps(data)) #JsonResponse(data)        

        # return super(DistrictAssignStationView,self).form_valid(form)

    def get_object(self):
        print("w--",self.kwargs)
        return DMABaseinfo.objects.get(pk=int(self.kwargs["pk"]))
        
    def get_context_data(self, *args, **kwargs):
        context = super(DistrictAssignStationView, self).get_context_data(*args, **kwargs)
        

        self.object = self.get_object()  # user_organ.dma.all().first()
        
        context["dma_pk"] = self.object.pk
        context["dma_no"] = self.object.dma_no
        context["dma_name"] = self.object.dma_name
        context["dma_group"] = self.object.belongto.name

        #dma station
        # dmastaions = self.object.station_set.all()
        dmastaions = self.object.station_assigned()
        data = []
        #dma分区的站点
        
        for a in dmastaions:
            commaddr = a.station_id     # 大表 通讯地址commaddr 或者 小区关联的集中器commaddr，由station_type 标识
            meter_type = a.meter_type
            station_type = a.station_type # 大表还是小区 1-大表 2-小区
            if station_type == '1':
                s = Bigmeter.objects.get(commaddr=commaddr)
                edit_id = s.pk
                username = s.username
                
            elif station_type == '2':
                # d = VConcentrator.objects.get(id=commaddr)
                d = Community.objects.get(id=commaddr)
                edit_id = d.pk
                username = d.name

            data.append({
                "id":edit_id,  #s.pk,
                "username":username,  #s.username,
                "pid":self.object.belongto.cid,
                "dmametertype":meter_type #s.dmametertype
            })

        dmastation_list = {
            "obj":{
                    "dmastationlist":data
            }
        }

        context["dmastation_list"] = json.dumps(dmastation_list)
        

        return context  


def saveDmaStation(request):
    dma_pk = request.POST.get("dma_pk")
    dma = DMABaseinfo.objects.get(pk=int(dma_pk))
    stationassign = request.POST.get("stationassign")
    jd = json.loads(stationassign)

    # old_dmastations = dma.station_set_all()
    # dmastations = dma.station_set.all() #old
    # dmastations = dma.station_set_all()
    old_assigned = dma.station_assigned()
    # print("dma old stations:",old_dmastations)

    refresh_list = []
    # 更新dma分区站点信息，
    for d in jd:
        print(d["station_id"],d["dma_name"],d["station_name"],d["metertype"],d["commaddr"],d["station_type"])
        station_id = int(d["station_id"])
        metertype = d["metertype"]
        station_type = d["station_type"]
        commaddr = d["commaddr"]
        refresh_list.append(commaddr) # add commaddr in fresh list
        station = DmaStation.objects.filter(dmaid=dma,station_id=commaddr)
        if not station.exists():
            # station.dmaid.add(dma)
            DmaStation.objects.create(dmaid=dma,station_id=commaddr,meter_type=metertype,station_type=station_type)
        else:
            s = station.first()
            s.station_type = station_type
            s.meter_type = metertype
            s.save()

        # station.dmametertype = metertype
        # station.save()
    
    print("refresh_list:",refresh_list)
    # 删除不在更新列表里的已分配的站点dmastation item
    for s in old_assigned:
        if s.station_id not in refresh_list:
            s.delete()
            # 修改dma相关站点信息

    data = {
            "success": 1,
            "obj":{"flag":1}
        }
    return HttpResponse(json.dumps(data)) #JsonResponse(data)   

# DMA 分配站点初始化连接
def getdmastationsbyId(request):

    dma_pk = request.POST.get("dma_pk")
    dma = DMABaseinfo.objects.get(pk = int(dma_pk))

    #dma station
    # dmastaions = dma.station_set_all()
    assigned_station = dma.station_assigned()

    data = []
    #dma分区的站点
    
    for a in assigned_station:
        commaddr = a.station_id
        station_type = a.station_type
        if station_type == "1":
            s= Bigmeter.objects.get(commaddr=commaddr)
            edit_id = s.pk
            username = s.username
        else:
            s = Community.objects.get(id=commaddr)
            edit_id = s.id
            username = s.name
        data.append({
            "id":edit_id,
            "username":username,
            "pid":dma.belongto.cid,
            "dmametertype":a.meter_type,
            "commaddr":a.station_id,
            "station_type":a.station_type
        })

    dmastation_list = {
        "obj":data,
        "success":True
    }

    return HttpResponse(json.dumps(dmastation_list)) 



def usertypeadd(request):
    if not request.user.has_menu_permission_edit('stationmanager_dmam'):
        return HttpResponse(json.dumps({"success":0,"msg":"您没有权限进行操作，请联系管理员."}))

    print('usertypeadd:',request.POST)
    usertypeform = WaterUserTypeForm(request.POST or None)
    print('usertypeform',usertypeform)

    usertype = request.POST.get("usertype")
    explains = request.POST.get("explains")
    obj = WaterUserType.objects.create(
            usertype = usertype,
            explains = explains)

    if obj:
        flag = 1
    else:
        flag = 0

    return HttpResponse(json.dumps({"success":flag}))

def findUsertypeById(request):
    print(request.POST)
    tid = request.POST.get("id")
    tid = int(tid)
    ut = WaterUserType.objects.get(pk=tid)

    operarions_list = {
        "exceptionDetailMsg":"",
        "msg":"",
        "obj":{
                "operation":{
                    "explains":ut.explains,
                    "id":ut.pk,
                    "userType":ut.usertype}
        },
        "success":True
    }
   

    return JsonResponse(operarions_list)

def updateOperation(request):
    print('updateOperation:',request.POST)
    tid = request.POST.get("id")
    usertype = request.POST.get("userType")
    explains = request.POST.get("explains")
    tid = int(tid)
    ut = WaterUserType.objects.get(pk=tid)
    ut.usertype = usertype
    ut.explains = explains
    ut.save()

    return JsonResponse({"success":True})


def deleteOperation(request):
    tid = request.POST.get("id")
    tid = int(tid)
    ut = WaterUserType.objects.get(pk=tid)
    ut.delete()

    return JsonResponse({"success":True})

def deleteOperationMore(request):
    print("deleteOperationMore:",request.POST)
    deltems = request.POST.get("ids")
    deltems_list = deltems.split(',')
    print(deltems_list)
    for uid in deltems_list:
        if uid !='':
            u = WaterUserType.objects.get(id=int(uid))
            u.delete()
    return JsonResponse({"success":True})

def usertypeedit(request):
    pass


def usertypedeletemore(request):
    if not request.user.has_menu_permission_edit('stationmanager_dmam'):
        return HttpResponse(json.dumps({"success":0,"msg":"您没有权限进行操作，请联系管理员."}))

    deltems = request.POST.get("deltems")
    deltems_list = deltems.split(';')

    for uid in deltems_list:
        u = MyUser.objects.get(id=int(uid))
        # print('delete user ',u)
        #删除用户 并且删除用户在分组中的角色
        for g in u.groups.all():
            g.user_set.remove(u)
        u.delete()

    return HttpResponse(json.dumps({"success":1}))


def userdeletemore(request):
    # print('userdeletemore',request,request.POST)

    if not request.user.has_menu_permission_edit('districtmanager_dmam'):
        return HttpResponse(json.dumps({"success":0,"msg":"您没有权限进行操作，请联系管理员."}))

    deltems = request.POST.get("deltems")
    deltems_list = deltems.split(';')

    for uid in deltems_list:
        u = MyUser.objects.get(id=int(uid))
        # print('delete user ',u)
        #删除用户 并且删除用户在分组中的角色
        for g in u.groups.all():
            g.user_set.remove(u)
        u.delete()

    return HttpResponse(json.dumps({"success":1}))

"""
Assets comment deletion, manager
"""


def userdeletemore(request):
    # print('userdeletemore',request,request.POST)

    if not request.user.has_menu_permission_edit('districtmanager_dmam'):
        return HttpResponse(json.dumps({"success":0,"msg":"您没有权限进行操作，请联系管理员."}))

    deltems = request.POST.get("deltems")
    deltems_list = deltems.split(';')

    for uid in deltems_list:
        u = MyUser.objects.get(id=int(uid))
        # print('delete user ',u)
        #删除用户 并且删除用户在分组中的角色
        for g in u.groups.all():
            g.user_set.remove(u)
        u.delete()

    return HttpResponse(json.dumps({"success":1}))


# 小区列表
def communitylist(request):
    draw = 1
    length = 0
    start=0
    print('userlist:',request.user)
    if request.method == "GET":
        draw = int(request.GET.get("draw", 1))
        length = int(request.GET.get("length", 10))
        start = int(request.GET.get("start", 0))
        search_value = request.GET.get("search[value]", None)
        # order_column = request.GET.get("order[0][column]", None)[0]
        # order = request.GET.get("order[0][dir]", None)[0]
        groupName = request.GET.get("groupName")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print("simpleQueryParam",simpleQueryParam)

    if request.method == "POST":
        draw = int(request.POST.get("draw", 1))
        length = int(request.POST.get("length", 10))
        start = int(request.POST.get("start", 0))
        pageSize = int(request.POST.get("pageSize", 10))
        search_value = request.POST.get("search[value]", None)
        # order_column = request.POST.get("order[0][column]", None)[0]
        # order = request.POST.get("order[0][dir]", None)[0]
        groupName = request.POST.get("groupName")
        districtId = request.POST.get("districtId")
        simpleQueryParam = request.POST.get("simpleQueryParam")
        # print(request.POST.get("draw"))
        print("groupName",groupName)
        print("districtId:",districtId)
        # print("post simpleQueryParam",simpleQueryParam)

    print("get userlist:",draw,length,start,search_value)

    user = request.user
    organs = user.belongto

    comunities = user.community_list_queryset(simpleQueryParam).values("id","name","belongto__name","address","vconcentrators__name")
    meged_community = merge_values(comunities)
    # meters = Community.objects.all() #.filter(communityid=105)  #文欣苑105

    def m_info(m):
        
        return {
            "id":m["id"],
            # "simid":m.simid,
            # "dn":m.dn,
            # "belongto":m.belongto.name,#current_user.belongto.name,
            # "metertype":m.metertype,
            "name":m["name"],
            "belongto":m["belongto__name"],
            "address":m["address"],
            "concentrator":m["vconcentrators__name"],
            "related":DmaStation.objects.filter(station_id=m["id"]).exists()
            # "station":m.station_set.first().username if m.station_set.count() > 0 else ""
        }
    data = []

    for m in meged_community:
        data.append(m_info(m))

    recordsTotal = comunities.count()
    # recordsTotal = len(meged_community)
    
    result = dict()
    result["records"] = data[start:start+length]
    result["draw"] = draw
    result["success"] = "true"
    result["pageSize"] = pageSize
    result["totalPages"] = recordsTotal/pageSize
    result["recordsTotal"] = recordsTotal
    result["recordsFiltered"] = recordsTotal
    result["start"] = 0
    result["end"] = 0

    print(draw,pageSize,recordsTotal/pageSize,recordsTotal)
    
    return HttpResponse(json.dumps(result))


def getDmaGisinfo(request):
    dma_no = request.POST.get("dma_no")

    dma = DmaGisinfo.objects.filter(dma_no=dma_no).values("geodata","strokeColor","fillColor")
    data = []

    if dma.exists():
        d = dma.first()
        data.append({"geoJsonData":json.loads(d["geodata"]),
        # data.append({"geoJsonData":d["geodata"],
            "strokeColor":d["strokeColor"],
            "fillColor":d["fillColor"]})
    else:
        data = []


    operarions_list = {
        "exceptionDetailMsg":"null",
        "msg":None,
        "obj":data,
        "success":True
    }
   

    return JsonResponse(operarions_list)


def saveDmaGisinfo(request):
    print("saveDmaGisinfo",request.POST)
    dma_no = request.POST.get("dma_no")
    geodata = request.POST.get("geodata")
    strokeColor = request.POST.get("strokeColor")
    fillColor = request.POST.get("fillColor")

    if dma_no is None:
        data = {
            "success": 0,
            "obj":{"flag":0}
        }
        return JsonResponse(data)

    dma = DmaGisinfo.objects.filter(dma_no=dma_no)
    if dma.exists():
        d = dma.first()
        d.geodata = geodata
        d.strokeColor = strokeColor
        d.fillColor = fillColor
        d.save()
    else:
        DmaGisinfo.objects.create(dma_no=dma_no,geodata=geodata,strokeColor=strokeColor,fillColor=fillColor)

    data = {
            "success": 1,
            "obj":{"flag":1}
        }

    return JsonResponse(data)