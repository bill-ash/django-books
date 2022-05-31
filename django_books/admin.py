from django.contrib import admin
from django_books.models import ServiceAccount, TicketQueue

admin.site.register(ServiceAccount)


class TicketQueueAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'status', 'method', 'model', 'last_update')
    list_display_links = ('ticket',)
    ordering = ['-last_update']

admin.site.register(TicketQueue, TicketQueueAdmin)