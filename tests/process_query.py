"""
Process some qbxml into a pandas dictionary 
"""

from datetime import datetime
from lxml import etree
import pandas as pd
from django_books.objects import *

with open("response.xml") as f:
    response = f.read()

qbxml_root = etree.fromstring(response)

assert qbxml_root.tag == "QBXML"


qbxml_msg_rs = qbxml_root[0]

assert qbxml_msg_rs.tag == "QBXMLMsgsRs"


response_body_root = qbxml_msg_rs[0]

assert "statusCode" in response_body_root.attrib


len(response_body_root)
list(response_body_root)
dir(response_body_root[1][0])

resp = []
for x in range(len(response_body_root)):
    children = response_body_root[x].getchildren()
    tmp = {}
    for child in children:
        tmp[child.tag] = child.text

    resp.append(tmp)

# Turn it into pandas
resp
pd.DataFrame(resp)


# def process_query_response(response):

#     qbxml_root = etree.fromstring(response)
#     assert qbxml_root.tag == 'QBXML'

#     qbxml_msg_rs = qbxml_root[0]
#     assert qbxml_msg_rs.tag == 'QBXMLMsgsRs'

#     response_body_root = qbxml_msg_rs[0]
#     assert 'statusCode' in response_body_root.attrib

#     resp = []
#     for x in range(len(response_body_root)):
#         children = response_body_root[x].getchildren()
#         tmp = {}
#         for child in children:
#             tmp[child.tag] = child.text

#         resp.append(tmp)
#     return resp

pd.DataFrame(process_query_response(response))
