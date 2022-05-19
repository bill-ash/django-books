from datetime import datetime
from lxml import etree

from datetime import datetime 
from uuid import uuid4

from django.shortcuts import render
from spyne.decorator import rpc, srpc
from spyne.model.complex import Array, Unicode
from spyne.model.primitive import Integer, String
from spyne.service import ServiceBase

from django.contrib.auth import get_user_model

from django_books.objects import *

from django_books.models import ServiceAccount, TicketQueue

import pandas as pd 

class QBWC_CODES:
    """
    Response codes from webconnector
    """
    NONE = 'none'  # no work to do for the service
    BUSY = 'busy'  # service is busy with other task
    NVU = 'nvu'  # invalid user is sent to the service
    CC = ''  # indicates current company to use for the web connector to proceed further
    CONN_CLS_OK = 'ok'  # indicates web connector and web service _set_connection closed successfully
    CONN_CLS_ERR = 'done'  # indicates web connector failed connecting to web service and finished its job
    INTR_DONE = 'done'  # indicates web connector finished interactive session with web service
    UNEXP_ERR = 'unexpected error'  # unexpected error received from web connector
    CV = ''  # no update needed for web connector to update its version, it can proceed further


class QuickBooksService(ServiceBase): 

    @rpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(ctx, strUserName, strPassword):
        """
        Authenticate with QuickBooks WebConnector. 
        Return value schedule: 
         - No work to be preformed: 
            - ['none', 'none']
         - Pending request: session token of work to reference and the current open company file  
            - ['guid', ''] 
            - ['guid', 'path/to/file_name.qbo'] 
         - Invalid user - not authenticated
            - ['', ''] | ['nvu', 'nvu']


        Args:
        @rpc >> ctx (DjangoHttpMethodContext): spyne.server.django.DjangoHttpMethodContext Inspect the information 
        returned to be parsed by spyne from the webconnector.
        The ctx (djangoHttpMethodContext) returns the method call of the webconnector as well as the parsed xml
            strUsername (str): Username to authenticate against. Needs to match realm id passed 
            when creating qbwc app installed.
            strPassword (str): Password to match against realm password
        """
        
        if ServiceAccount.objects.get(qbid=strUserName):
            # Create a service account and make sure the username matches the UUID passed to the 
            # <UserName> </UserName> field in the .qwc file installed to WebConnector.
            if ServiceAccount.objects.get(qbid=strUserName).password == strPassword:
                # If there is new work to be processed check for it here. 
                if TicketQueue.objects.filter(status='5').count() > 0: # Approved
                    ticket = TicketQueue.objects.filter(status='5').first().ticket
                    print('Success!')
                    return [str(ticket), '']
                else:
                    return ['none', 'none']
        return []
        
        # return_array = []
        # create a new session manager which handles the go between Redis and webconnector
        # realm = session_manager.authenticate(username=strUsername, password=strPassword)
        return ['none','none']

    @srpc(Unicode, Unicode, Unicode, Unicode, _returns=Integer)
    def receiveResponseXML(ticket, response, hresult, message): 
        """
        Returns the data response form the QuickBooks WebConnector. 

        Args:
            ticket (str): ticket
            response (QBXML): Response from QuickBooks
            hresult (str): Hex error message that could accompany any successful work 
            message (str): Error message 
        
        @return (int) Positive integer 100 for completed work, and less than 100 to move to the next ticket. 
            Needs to be handled by the session manager.  
        """

        print('receiveResponseXML()')
        print("ticket=" + ticket)
        print("response=" + response)
        
        if hresult:
            print("hresult=" + hresult)
            print("message=" + message)
        
        try:
            resp = process_response(response)
            resp = process_query_response(response)
        except Exception as e:
            print(e)
            resp = {}

        breakpoint()
        # if resp.get('statusSeverity') == 'Error' or hresult is not None:
        #     error = Expense.objects.filter(status='APPROVED').first()
        #     error.status = 'CLOSED'
        #     error.save()
        # else: 
        #     success = Expense.objects.filter(status='APPROVED').first()
        #     success.status = 'CLOSED'
        #     success.save()

        # if Expense.objects.filter(status='APPROVED').count() > 0:
        # # return session_manager.process_response(ticket, response, hresult, message)
        #     return 90
        return 100

    @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=String)
    def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
        print('sendRequestXML() has been called')
        print('ticket:', ticket)
        print('strHCPResponse', strHCPResponse)
        print('strCompanyFileName', strCompanyFileName)
        print('qbXMLCountry', qbXMLCountry)

        realm = TicketQueue.objects.get(ticket=ticket)
        # Look up all objects associated with ticket awaiting processing 
        # session_manager.check_iterating_request(request, ticket)
        # expense = Expense.objects.filter(status='APPROVED').first()
        xml = query_custom_txn()
        # breakpoint()
        # xml = add_credit_card_payment(expense.txn_card, 
        #     expense.bill_vendor,
        #     expense.txn_date.strftime('%Y-%m-%d'), 
        #     expense.bill_ref,
        #     expense.txn_member_name,
        #     expense.gl_account,
        #     expense.txn_amount,
        #     expense.description or 'DEFAULT DESC', 
        #     )
        # print(xml)
        # xml = add_customer(name='SuperUser' + datetime.now().strftime('%y%m%d%s'))
        
        return xml

    @srpc(Unicode, _returns=Unicode)
    def clientVersion(strVersion, *args, **kwargs):
        """
        Check the current WebConnector version is compatiable with the application.

        Args:
            strVersion (str): QBWC version?
        """
        # print(type(ctx))
        # print(*args)
        # print(**kwargs)
        if strVersion == '2.3.0.207':
            print('Success!')
        # breakpoint()
        print('requesting auth')
        print('clientVersion(): version=%s' % strVersion)
        return ''


    @rpc(Unicode, _returns=Unicode)
    def closeConnection(ctx, ticket): 
        """
        Close the current connection with QuickBooks Webconnector.

        Args:
            ctx (DjangoHttpMethodContext): spyne processed request wasdl
            ticket (str): ticket that is completed?
        """
        print('closeConnection(): ticket=%s' % ticket)
        # This is where we can clean up any work 
        # realm = session_manager.get_realm(ticket)
        # session_manager.close_session(realm)
        return 'ok'

    
    @srpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def connectionError(ticket, hresult, message): 
        """
        Tell the web service about an error the web connector encountered in its attempt to connect to QuickBooks
        or QuickBooks POS
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @param hresult the HRESULT (in HEX) from the exception thrown by the request processor
        @param message The error message that accompanies the HRESULT from the request processor
        @return string value "done" to indicate web service is finished or the full path of the different company for
        retrying _set_connection.
        """
        print('connectionError(): ticket=%s, hresult=%s, message=%s' % (ticket, hresult, message))
        # realm = session_manager.get_realm(ticket)
        # session_manager.close_session(realm)
        return 'done'

    @srpc(Unicode, _returns=Unicode)
    def getLastError(ticket): 
        """
        Allow the web service to return the last web service error, normally for displaying to user, before
        causing the update action to stop.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string message describing the problem and any other information that you want your user to see.
        The web connector writes this message to the web connector log for the user and also displays it in the web
        connector’s Status column.
        """
        # In the case of expenses, errors should be wrapped in some try logic and displayed on completion 
        # of the work being preformed -- would not get batched. 
        print('getLastError(): ticket=%s' % ticket)


    @srpc(Unicode, _returns=Unicode)
    def getServerVersion(ticket): 
        """
        Provide a way for web-service to notify web connector of it’s version and other details about version
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string message string describing the server version and any other information that user may want to see
        """

        # Don't remember reading about this -- not sure if it's required
        version ='2.2.0.34'

        print('getServerVersion(): version=%s' % version)
        return version

    @srpc(Unicode, _returns=Unicode)
    def interactiveDone(ticket): 
        """
        Allow the web service to indicate to web connector that it is done with interactive mode.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string value "Done" should be returned when interactive session is over
        """
        # for completeness - don't intend on using 
        print('interactiveDone(): ticket=%s' % ticket)
        return 'done'
        
    @rpc(Unicode, Unicode, _returns=Unicode)
    def interactiveRejected(ctx, ticket, reason):
        """
        Allow the web service to take alternative action when the interactive session it requested was
        rejected by the user or by timeout in the absence of the user.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @param reason the reason for the rejection of interactive mode
        @return string value "Done" should be returned when interactive session is over
        """
        print('interactiveRejected()')
        print(ticket)
        print(reason)
        return 'Interactive mode rejected'

 
    @srpc(Unicode, Unicode, _returns=Unicode)
    def interactiveUrl(ticket, sessionID):
        print('interactiveUrl')
        print(ticket)
        print(sessionID)
        return ''




def support(request):
    return render(request, 'django_books/support.html', {})

