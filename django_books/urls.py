from django.urls import path
from spyne.protocol.soap import Soap11
from spyne.server.django import DjangoView 

from django_books.views import QuickBooksService, support

urlpatterns = [
    path('support/', support, name='support'),
    path('webconnector/', DjangoView.as_view(
        services=[QuickBooksService],
        tns='http://developer.intuit.com/',
        in_protocol=Soap11(validator='lxml'),
        out_protocol=Soap11())
        ),
]