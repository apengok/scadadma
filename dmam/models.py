# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.urls import reverse
from entm.models import Organization
import datetime
from django.db.models import Q
from legacy.models import Bigmeter,District,Community,HdbFlowData,HdbFlowDataHour,HdbFlowDataDay,HdbFlowDataMonth,HdbPressureData
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.db.models import Avg, Max, Min, Sum
from legacy.models import Bigmeter,District,Community,Concentrator,Watermeter,SecondDistrict,SecondWater
from django.utils.functional import cached_property
import time
from legacy.utils import (HdbFlow_day_use,HdbFlow_day_hourly,HdbFlow_month_use,HdbFlow_monthly,hdb_watermeter_flow_monthly,
        Hdbflow_from_hdbflowmonth,hdb_watermeter_flow_daily,Hdbflow_from_hdbflowday,
        ZERO_monthly_dict,generat_year_month,generat_year_month_from)
from mptt.models import MPTTModel, TreeForeignKey

from .utils import merge_values
import random

# Create your models here.

class DMABaseinfoQuerySet(models.query.QuerySet):
    def search(self, cid,organlevel,dma_no): #RestaurantLocation.objects.all().search(query) #RestaurantLocation.objects.filter(something).search()
        if dma_no:
            dma_no = dma_no.strip()
            return self.filter(
                Q(dma_no__iexact=dma_no)
                ).distinct()
        else:
            cid = cid.strip()
            organlevel = organlevel.strip()
            return self.filter(
                Q(belongto__cid__icontains=cid)|
                Q(belongto__organlevel__iexact=organlevel)
                # Q(meter__simid__simcardNumber__iexact=query)
                ).distinct()
        return self



class DMABaseinfoManager(models.Manager):
    def get_queryset(self):
        return DMABaseinfoQuerySet(self.model, using=self._db)

    def search(self, cid,organlevel,dma_no): #RestaurantLocation.objects.search()
        return self.get_queryset().search(cid,organlevel,dma_no)


class DMABaseinfo(models.Model):
    dma_no        = models.CharField('分区编号',max_length=50, unique=True)
    dma_name      = models.CharField('分区名称',max_length=50, unique=True)

    pepoles_num   = models.CharField('服务人口',max_length=50, null=True,blank=True)
    acreage       = models.CharField('服务面积',max_length=50, null=True,blank=True)
    user_num      = models.CharField('用户数量',max_length=50, null=True,blank=True)
    pipe_texture  = models.CharField('管道材质',max_length=50, null=True, blank=True)
    pipe_length   = models.CharField('管道总长度(m)',max_length=50, null=True, blank=True)
    pipe_links    = models.CharField('管道连接总数(个)',max_length=50,null=True, blank=True)
    pipe_years    = models.CharField('管道最长服务年限(年)',max_length=50,null=True, blank=True)
    pipe_private  = models.CharField('私人拥有水管长度(m)',max_length=50,blank=True,null=True)
    ifc           = models.CharField('IFC参数',max_length=250, null=True, blank=True)
    aznp          = models.CharField('AZNP',max_length=250,null=True, blank=True)
    night_use     = models.CharField('正常夜间用水量',max_length=50,null=True, blank=True)
    cxc_value     = models.CharField('产销差目标值',max_length=50, null=True, blank=True)

    creator      = models.CharField('负责人',max_length=50, null=True, blank=True) 
    create_date  = models.CharField('建立日期',max_length=30, null=True, blank=True) 

    belongto = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='dma',
        # primary_key=True,
    )

    objects = DMABaseinfoManager()

    class Meta:
        managed=True
        unique_together = ('dma_no', )
        db_table = 'dma_baseinfo'

    @property
    def dma_level(self):
        return self.belongto.organlevel

        

    def get_absolute_url(self): #get_absolute_url
        # return "/organ/{}".format(self.pk)
        return reverse('dma:dma_manager', kwargs={'pk': self.pk})

    def __unicode__(self):
        return self.dma_name

    def __str__(self):
        return self.dma_name        

    def station_assigned(self):
        dmastations = self.dmastation_set.all()
        return dmastations

    def station_set_all(self):
        
        dmastations = self.dmastation_set.all()
        commaddr_list = []
        for d in dmastations:
            commaddr = d.station_id
            commaddr_list.append(commaddr)
        stationlist = Bigmeter.objects.filter(commaddr__in=commaddr_list)
            
        return stationlist

    # obsolete
    def dma_statistic(self,month_list1):
        """
            month_list1 是一整年的月份列表
            month_list 是dma创建日期的月份其实列表，统计数据是从创建日期开始计算的
        """
        dmastations_list = self.station_set.all()
        
        # dmastations_list2 = self.station_set.values_list('meter__simid__simcardNumber','dmametertype')
        cre_data = datetime.datetime.strptime(self.create_date,"%Y-%m-%d")
        month_list = generat_year_month_from(cre_data.month,cre_data.year)
        # print("create data month_list",month_list)
        
        # meter_types = ["出水表","进水表","贸易结算表","未计费水表","官网检测表"] 管网监测表
        # 进水表  加和---> 进水总量
        water_in = 0
        monthly_in = ZERO_monthly_dict(month_list1)
        meter_in = dmastations_list.filter(dmametertype='进水表')
        
        for m in meter_in:
            commaddr = m.commaddr
            
            monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            
            # print(m.username,commaddr,monthly_use)
            for k in monthly_in.keys():
                if k in monthly_use.keys():
                    monthly_in[k] += monthly_use[k]
                # else:
                #     monthly_in[k] = 0
        water_in = sum([monthly_in[k] for k in monthly_in.keys()])
        
        # 出水表 加和--->出水总量
        water_out = 0
        monthly_out = ZERO_monthly_dict(month_list1)
        meter_out = dmastations_list.filter(dmametertype='出水表')
        for m in meter_out:
            commaddr = m.commaddr
            monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_out.keys():
                if k in monthly_use.keys():
                    monthly_out[k] += monthly_use[k]
                # else:
                #     monthly_out[k] = monthly_use[k]
        water_out = sum([monthly_out[k] for k in monthly_out.keys()])
        
        # 售水量 = 所有贸易结算表的和
        water_sale = 0
        monthly_sale = ZERO_monthly_dict(month_list1)
        meter_sale = dmastations_list.filter(dmametertype='贸易结算表')

        for m in meter_sale:
            commaddr = m.commaddr
            if m.username == "文欣苑户表总表":
                monthly_use = hdb_watermeter_flow_monthly(105,month_list)

            else:
                monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_sale.keys():
                if k in monthly_use.keys():
                    monthly_sale[k] += monthly_use[k]
                # else:
                #     monthly_sale[k] = monthly_use[k]

        water_sale += sum([monthly_sale[k] for k in monthly_sale.keys()])
        
        # 未计量水量 = 所有未计费水表的和
        water_uncount = 0
        monthly_uncount = ZERO_monthly_dict(month_list1)
        meter_uncount = dmastations_list.filter(dmametertype='未计费水表')
        for m in meter_uncount:
            commaddr = m.commaddr
            monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_uncount.keys():
                if k in monthly_use.keys():
                    monthly_uncount[k] += monthly_use[k]
                # else:
                #     monthly_uncount[k] = monthly_use[k]
        water_uncount = sum([monthly_uncount[k] for k in monthly_uncount.keys()])
        
        # 漏损量 = 供水量-售水量-未计费水量 分区内部进水表要减去自己内部出水表才等于这个分区的供水量

        return {
            'water_in':water_in,
            'monthly_in':monthly_in,
            'water_out':water_out,
            'monthly_out':monthly_out,
            'water_sale':water_sale,
            'monthly_sale':monthly_sale,
            'water_uncount':water_uncount,
            'monthly_uncount':monthly_uncount,

        }


    def dma_statistic2(self,month_list1):
        """
            month_list1 是一整年的月份列表
            month_list 是dma创建日期的月份其实列表，统计数据是从创建日期开始计算的
        """
        dmastations_list = self.station_assigned()
        
        # dmastations_list2 = self.station_set.values_list('meter__simid__simcardNumber','dmametertype')
        cre_data = datetime.datetime.strptime(self.create_date,"%Y-%m-%d")
        month_list = generat_year_month_from(cre_data.month,cre_data.year)
        # print("create data month_list",month_list)
        
        # meter_types = ["出水表","进水表","贸易结算表","未计费水表","官网检测表"] 管网监测表
        # 进水表  加和---> 进水总量
        water_in = 0
        monthly_in = ZERO_monthly_dict(month_list1)
        meter_in = dmastations_list.filter(meter_type='进水表')
        
        for m in meter_in:
            commaddr = m.station_id
            
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                monthly_use = hdb_watermeter_flow_monthly(community_id,month_list)

            else:
                monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            
            # print(m.username,commaddr,monthly_use)
            for k in monthly_in.keys():
                if k in monthly_use.keys():
                    monthly_in[k] += monthly_use[k]
                # else:
                #     monthly_in[k] = 0
        water_in = sum([monthly_in[k] for k in monthly_in.keys()])
        
        # 出水表 加和--->出水总量
        water_out = 0
        monthly_out = ZERO_monthly_dict(month_list1)
        meter_out = dmastations_list.filter(meter_type='出水表')
        for m in meter_out:
            commaddr = m.station_id
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                monthly_use = hdb_watermeter_flow_monthly(community_id,month_list)

            else:
                monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_out.keys():
                if k in monthly_use.keys():
                    monthly_out[k] += monthly_use[k]
                # else:
                #     monthly_out[k] = monthly_use[k]
        water_out = sum([monthly_out[k] for k in monthly_out.keys()])
        
        # 售水量 = 所有贸易结算表的和
        water_sale = 0
        monthly_sale = ZERO_monthly_dict(month_list1)
        meter_sale = dmastations_list.filter(meter_type='贸易结算表')

        for m in meter_sale:
            commaddr = m.station_id
            # print("&*^&*%&$*(&^&---",commaddr,m.station_type)
            # if m.username == "文欣苑户表总表":
            # if commaddr == '4022':
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                monthly_use = hdb_watermeter_flow_monthly(community_id,month_list)

            else:
                monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_sale.keys():
                if k in monthly_use.keys():
                    monthly_sale[k] += monthly_use[k]
                # else:
                #     monthly_sale[k] = monthly_use[k]

        water_sale += sum([monthly_sale[k] for k in monthly_sale.keys()])
        
        # 未计量水量 = 所有未计费水表的和
        water_uncount = 0
        monthly_uncount = ZERO_monthly_dict(month_list1)
        meter_uncount = dmastations_list.filter(meter_type='未计费水表')
        for m in meter_uncount:
            commaddr = m.station_id
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                monthly_use = hdb_watermeter_flow_monthly(community_id,month_list)

            else:
                monthly_use = Hdbflow_from_hdbflowmonth(commaddr,month_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,monthly_use)
            for k in monthly_uncount.keys():
                if k in monthly_use.keys():
                    monthly_uncount[k] += monthly_use[k]
                # else:
                #     monthly_uncount[k] = monthly_use[k]
        water_uncount = sum([monthly_uncount[k] for k in monthly_uncount.keys()])
        
        # 漏损量 = 供水量-售水量-未计费水量 分区内部进水表要减去自己内部出水表才等于这个分区的供水量

        return {
            'water_in':water_in,
            'monthly_in':monthly_in,
            'water_out':water_out,
            'monthly_out':monthly_out,
            'water_sale':water_sale,
            'monthly_sale':monthly_sale,
            'water_uncount':water_uncount,
            'monthly_uncount':monthly_uncount,

        }

    
    def dma_statistic_daily(self,day_list):
        """
            需要统计的日期列表
            month_list 是dma创建日期的月份其实列表，统计数据是从创建日期开始计算的
        """
        dmastations_list = self.station_assigned()
        
        # dmastations_list2 = self.station_set.values_list('meter__simid__simcardNumber','dmametertype')
        
        # print("create data month_list",month_list)
        
        # meter_types = ["出水表","进水表","贸易结算表","未计费水表","官网检测表"] 管网监测表
        # 进水表  加和---> 进水总量
        water_in = 0
        daily_in = ZERO_monthly_dict(day_list)
        meter_in = dmastations_list.filter(meter_type='进水表')
        
        for m in meter_in:
            commaddr = m.station_id
            
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                daily_use = hdb_watermeter_flow_daily(community_id,day_list)

            else:
                daily_use = Hdbflow_from_hdbflowday(commaddr,day_list) #HdbFlow_monthly(commaddr)
            
            # print(m.username,commaddr,daily_use)
            for k in daily_in.keys():
                if k in daily_use.keys():
                    daily_in[k] += daily_use[k]
                # else:
                #     daily_in[k] = 0
        water_in = sum([daily_in[k] for k in daily_in.keys()])
        
        # 出水表 加和--->出水总量
        water_out = 0
        daily_out = ZERO_monthly_dict(day_list)
        meter_out = dmastations_list.filter(meter_type='出水表')
        for m in meter_out:
            commaddr = m.station_id
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                daily_use = hdb_watermeter_flow_daily(community_id,day_list)

            else:
                daily_use = Hdbflow_from_hdbflowday(commaddr,day_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,daily_use)
            for k in daily_out.keys():
                if k in daily_use.keys():
                    daily_out[k] += daily_use[k]
                # else:
                #     daily_out[k] = daily_use[k]
        water_out = sum([daily_out[k] for k in daily_out.keys()])
        
        # 售水量 = 所有贸易结算表的和
        water_sale = 0
        daily_sale = ZERO_monthly_dict(day_list)
        meter_sale = dmastations_list.filter(meter_type='贸易结算表')

        for m in meter_sale:
            commaddr = m.station_id
            # print("&*^&*%&$*(&^&---",commaddr,m.station_type)
            # if m.username == "文欣苑户表总表":
            # if commaddr == '4022':
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                daily_use = hdb_watermeter_flow_daily(community_id,day_list)

            else:
                daily_use = Hdbflow_from_hdbflowday(commaddr,day_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,daily_use)
            for k in daily_sale.keys():
                if k in daily_use.keys():
                    daily_sale[k] += daily_use[k]
                # else:
                #     daily_sale[k] = daily_use[k]

        water_sale += sum([daily_sale[k] for k in daily_sale.keys()])
        
        # 未计量水量 = 所有未计费水表的和
        water_uncount = 0
        daily_uncount = ZERO_monthly_dict(day_list)
        meter_uncount = dmastations_list.filter(meter_type='未计费水表')
        for m in meter_uncount:
            commaddr = m.station_id
            if m.station_type == "2": #小区-- commaddr=VCommunity id
                community_id = commaddr
                daily_use = hdb_watermeter_flow_daily(community_id,day_list)

            else:
                daily_use = Hdbflow_from_hdbflowday(commaddr,day_list) #HdbFlow_monthly(commaddr)
            # print(m.username,commaddr,daily_use)
            for k in daily_uncount.keys():
                if k in daily_use.keys():
                    daily_uncount[k] += daily_use[k]
                # else:
                #     daily_uncount[k] = daily_use[k]
        water_uncount = sum([daily_uncount[k] for k in daily_uncount.keys()])
        
        # 漏损量 = 供水量-售水量-未计费水量 分区内部进水表要减去自己内部出水表才等于这个分区的供水量

        return {
            'water_in':water_in,
            'daily_in':daily_in,
            'water_out':water_out,
            'daily_out':daily_out,
            'water_sale':water_sale,
            'daily_sale':daily_sale,
            'water_uncount':water_uncount,
            'daily_uncount':daily_uncount,

        }


    def dmaMapStatistic(self):
        '''
            DMA 在线监控页面 dma分区的统计信息
        '''
        month_list = generat_year_month()
        # print(month_list)
        dmareport = self.dma_statistic2(month_list)

        water_in = dmareport['water_in']
        monthly_sale = dmareport['monthly_sale']
        # print('monthly_sale',monthly_sale)
        today = datetime.date.today()
        month_str = today.strftime("%Y-%m")
        
        lastmonth = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        lastmonth_str = lastmonth.strftime("%Y-%m")

        if self.belongto.organlevel == '1':
            dma_level = '2'
        else:
            dma_level = self.belongto.organlevel

        return {
            "dma_name":self.dma_name,
            "dma_no":self.dma_no,
            "belongto":self.belongto.name,
            "belongto_cid":self.belongto.cid,
            "dma_level":dma_level, #"二级",
            "state":"在线",
            "water_in":round(float(water_in),2),
            "readtime":'2018-12-29',
            "month_sale":round(float(monthly_sale[month_str]),2) ,
            "last_month_sale":round(float(monthly_sale[lastmonth_str]),2) ,
            "last_add_ratio":"34%",
            "leakerate":random.choice([9.65,13.46,11.34,24.56,32.38,7.86,10.45,17.89,23.45,36,78])
        }

    def dma_map_realdata(self):
        today = datetime.date.today()
        c_month = today.strftime("%Y-%m")
        
        yesmonth = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        bc_month = yesmonth.strftime("%Y-%m")
        lastmonth = yesmonth.replace(day=1) - datetime.timedelta(days=1)
        bbc_month = lastmonth.strftime("%Y-%m")

        month_list = [bbc_month,bc_month,c_month]
        # print(month_list)
        monthreport = self.dma_statistic2(month_list)
        
        # 供水量 = 进水总量 - 出水总量
        # 漏损量 = 供水量-售水量-未计费水量

        current_month=[]    # 本月
        bcurrent_month=[]   # 上月
        bbcurrent_month=[]  #前月

        for m in month_list:
            # 本月进水
            monthly_in = round(float(monthreport["monthly_in"][m]),2)
            monthly_out = round(float(monthreport["monthly_out"][m]),2)
            monthly_sale = round(float(monthreport["monthly_sale"][m]),2)
            monthly_uncount = round(float(monthreport["monthly_uncount"][m]),2)

            monthly_provider = round(float(float(monthly_in) - float(monthly_out)),2)
            monthly_leak = round(float(float(monthly_provider - float(monthly_sale) - float(monthly_uncount))),2)
            monthly_in = round(monthly_in/10000,2)
            monthly_out = round(monthly_out/10000,2)
            monthly_provider = round(monthly_provider/10000,2)
            monthly_leak = round(monthly_leak/10000,2)

            if m == c_month:
                # 供水，进水，出水，漏损
                current_month_sale = round(float(monthly_sale),2)
                current_month=[monthly_provider,monthly_in,monthly_out,monthly_leak]
            elif m == bc_month:
                bcurrent_month=[monthly_provider,monthly_in,monthly_out,monthly_leak]
            else:
                bbcurrent_month=[monthly_provider,monthly_in,monthly_out,monthly_leak]
        
        
        yestoday = today - datetime.timedelta(days=1)
        byestoday = today - datetime.timedelta(days=2)
        bbyestoday = today - datetime.timedelta(days=3)
        d1 = today.strftime("%Y-%m-%d")
        d2 = yestoday.strftime("%Y-%m-%d")
        d3 = byestoday.strftime("%Y-%m-%d")
        d4 = bbyestoday.strftime("%Y-%m-%d")
        day_list = [d1,d2,d3,d4]
        daily_report = self.dma_statistic_daily(day_list)

        current_day     = [] #今日
        bcurrent_day     = [] #昨日
        bbcurrent_day     = [] #前日
        bbbcurrent_day     = [] #前前日

        for d in day_list:
            daily_in = round(float(daily_report["daily_in"][d]),2)
            daily_out = round(float(daily_report["daily_out"][d]),2)
            daily_sale = round(float(daily_report["daily_sale"][d]),2)
            daily_uncount = round(float(daily_report["daily_uncount"][d]),2)

            daily_provider = round(float(daily_in) - float(daily_out),2)
            daily_leak = round(daily_provider - float(daily_sale) - float(daily_uncount),2)

            if d == d1:
                current_day = [daily_provider,daily_in,daily_out,daily_leak]
            elif d == d2:
                bcurrent_day = [daily_provider,daily_in,daily_out,daily_leak]
            elif d == d3:
                bbcurrent_day = [daily_provider,daily_in,daily_out,daily_leak]
            else:
                bbbcurrent_day = [daily_provider,daily_in,daily_out,daily_leak]
        
        


        return {
            "dma_name":self.dma_name,
            "dma_no":self.dma_no,
            "current_month":current_month,
            "current_month_sale":current_month_sale,
            "bcurrent_month":bcurrent_month,
            "bbcurrent_month":bbcurrent_month,
            "current_day":current_day,
            "bcurrent_day":bcurrent_day,
            "bbcurrent_day":bbcurrent_day,
            "bbbcurrent_day":bbbcurrent_day,
            "bbbday_str":bbyestoday.strftime("%m月%d日"),
        }

'''
 
直接在Station 用ManyToManyField关联到dmabaseinfo
一个站点可能在多个dma中分担角色，‘直接在Station 用ManyToManyField关联到dmabaseinfo’不能区分该站点是数据哪个dma的表，
所以还是启用该table
'''
class DmaStation(models.Model):
    dmaid           = models.ForeignKey(DMABaseinfo,blank=True, null=True,on_delete=models.CASCADE) 
    station_id      = models.CharField(max_length=30)   # 大表 通讯地址commaddr 或者 小区id(由于小区可能关联多个集中器，所以不能直接保存集中器的commaddr)，由station_type 标识
    meter_type      = models.CharField(max_length=30)   # dma计算类型 ["出水表","进水表","贸易结算表","未计费水表","管网检测表"]
    station_type    = models.CharField(max_length=30)   # 大表还是小区 1-大表 2-小区

    class Meta:
        managed=True
        db_table = 'dma_station'  

    def __unicode__(self):
        return self.dmaid.dma_name

    def __str__(self):
        return self.dmaid.dma_name   


class DmaGisinfo(models.Model):
    dma_no        = models.CharField('分区编号',max_length=50, unique=True)
    geodata       = models.TextField(blank=True,null=True)
    strokeColor   = models.CharField(max_length=100,blank=True,null=True)
    fillColor     = models.CharField(max_length=100,blank=True,null=True)

    class Meta:
        managed=True
        db_table = 'dma_gisinfo'  

    def __unicode__(self):
        return "{} polygon path".format(self.dma_no)

    def __str__(self):
        return "{} polygon path".format(self.dma_no)

