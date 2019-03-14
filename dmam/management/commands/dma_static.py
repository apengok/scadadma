#-*- coding:utf-8 -*-
from django.core.management.base import BaseCommand, CommandError

from dmam.models import DMABaseinfo
from legacy.utils import generat_year_month
import datetime
import time

class Command(BaseCommand):
    help = "query dma stastics data"

    def add_arguments(self,parser):
        parser.add_argument("dma_no",type=str,help="dmm_no to query ")
        parser.add_argument("-m","--month",type=str,help="month to query")
        parser.add_argument("-d","--day",type=str,help="day to query")



    def handle(self,*args,**options):
        dma_no = options["dma_no"]
        month = options["month"]
        day = options["day"]

        if dma_no:
            dma = DMABaseinfo.objects.get(dma_no=dma_no)
            if dma is None:
                print("DMA({}) not exist".format(dma_no))
                return

            dma_map_rd=dma.dma_map_realdata()
            print(dma_map_rd)

