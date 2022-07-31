import logging 

from django.db import models
from django_books.models import BaseObjectMixin

logger = logging.getLogger(__name__)

class Vendor(BaseObjectMixin): 
    pass 

    def get_query(ticket, model, *args, **kwargs): 
        pass 

    def post_query(ticket, model, *args, **kwargs): 
        pass 

    def process_get(ticket, response, *args, **kwargs): 
        pass 

    def process_post(ticket, response, *args, **kwargs): 
        pass 

class ExpenseAccount(BaseObjectMixin): 
    pass 

    def get_query(ticket, model, *args, **kwargs): 
        pass 

    def post_query(ticket, model, *args, **kwargs): 
        pass 

    def process_get(ticket, response, *args, **kwargs): 
        pass 

    def process_post(ticket, response, *args, **kwargs): 
        pass 

class Expense(BaseObjectMixin): 
    account = models.ForeignKey(
        ExpenseAccount,
        null=True,
        blank=True, 
        on_delete=models.SET_NULL
        ) 
    vendor = models.ForeignKey(
        Vendor,
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )

    memo = models.CharField(max_length=120)
    amount = models.FloatField()
    type = models.CharField(max_length=40)

    def get_query(ticket, model, *args, **kwargs): 
        pass 

    def post_query(ticket, model, *args, **kwargs): 
        pass 

    def process_get(ticket, response, *args, **kwargs): 
        pass 

    def process_post(ticket, response, *args, **kwargs): 
        pass 