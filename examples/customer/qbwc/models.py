import logging 
import re
from django.db import models
from django_books.models import BaseObjectMixin

from django_books.objects import query, add_customer

logger = logging.getLogger(__name__)

class Customer(BaseObjectMixin): 

    name = models.CharField(max_length=50)
    type = models.CharField(max_length = 20, default='test')
    

    # Defines how to make and requests and handle responses... 
    def get_query(name='Customer', *args, **kwargs):
        return query(name)


    def post_query(ticket, *args, **kwargs): 
        c = Customer.objects.filter(
            _batch_id=ticket,
            _batch_status=Customer.BatchStatus.UN_BATCHED
        ).first()
        return add_customer(c.name)



    def patch_query(*args, **kwargs): 
        raise NotImplementedError



    def process_get(resp = None, *args, **kwargs): 
        """
        What to do with the response from QB - parsed as a list of dictionaries...
        """ 
        return resp


    def process_post(ticket, response, **kwargs): 
        # [{
        #   'ListID': '800000DC-1702686768',
        #   'TimeCreated': '2023-12-15T19:32:48-05:00', 
        #   'TimeModified': '2023-12-15T19:32:48-05:00',
        #   'EditSequence': '1702686768', 
        #   'Name': 'Barry001658709167',
        #   'FullName': 'Barry001658709167',
        #   'IsActive': 'true',
        #   'Sublevel': '0', 'Balance': '0.00', 'TotalBalance': '0.00', 'SalesTaxCodeRef': '\n',
        #   'ItemSalesTaxRef': '\n', 
        #   'JobStatus': 'None',
        #   'PreferredDeliveryMethod': 'None'
        # }]
        if response: 
            # if isinstance(response, dict):
            try:
                qb = {
                    'ListID' : response.get('ListID'),
                    'Name' : response.get('Name'),
                    'TimeCreated' : response.get('TimeCreated'),
                    'TimeModified' : response.get('TimeModified'),
                } 
                
                Customer.objects.filter(_batch_id=ticket).update(
                        _batch_status = Customer.BatchStatus.BATCHED, 
                        _list_id=qb['ListID'], 
                        _time_created=qb['TimeCreated'], 
                        _time_modified=qb['TimeModified']
                )
                
            except Exception as e: 
                logger.error('Error parsing response to model.')
                raise KeyError('Error Parsing response to model.')

    def process_patch(*args, **kwargs): 
        raise NotImplementedError

    def __str__(self): 
        return self.name


