# Django Books

Functional django application for interacting with the QuickBooks Desktop Webconnector.


# TODOS

Create a service account which is responsible for communicating with the Webconnector. 
- Add a method that produces a .qwc file that is installed to webconnector
- Like an admin? Maybe a profile page for an admin that will spit out a .qwc file?

Abstracting models is dificult. Each application will have it's own unique workflows that depend 
on business requirements. 

Create a model mixin that will add new 'batches' to be added to a ticket queue. The ticket 
queue is the work to be preformed on the next web connector sync. 

Ticket log for syncing QB data with external resources/dashboards is different from importing new records 
from django. 

# Resources 

Heavily inspired by previous attempts at talking to Quick Books desktop with the goal of using 
python3 and current django version and no redis dependency. 

- https://github.com/weltlink/django-quickbooks 
- https://github.com/BillBarry/pyqwc
- http://spyne.io/#inprot=HttpRpc&outprot=JsonDocument&s=rpc&tpt=WsgiApplication&validator=true

Intuit documentation is quite dated but still useful. 

- https://developer.intuit.com/app/developer/qbdesktop/docs/develop/sample-applications-and-code
- https://github.com/IntuitDeveloper/QBXML_SDK_Samples/tree/64bitUpgrade/xmlfiles
- https://developer.intuit.com/app/developer/qbdesktop/docs/api-reference/qbdesktop

Program guide with detailed outline of all the required endpoints for communicating with the 
web connector. 

- https://static.developer.intuit.com/qbSDK-current/doc/pdf/QBWC_proguide.pdf


Additionaly, the forums are somewhat active: 

- https://help.developer.intuit.com/s/