import re
import requests
import json
from requests.structures import CaseInsensitiveDict
import boto3


url = "https://search-estestdo-52rnoiqtey5px7lyufmfpbcs5m.us-east-1.es.amazonaws.com/proddata/_doc"
headers = CaseInsensitiveDict()
headers["Content-Type"] = "application/json"
headers["Authorization"] = "Basic ZGVuaW06SElHSHNlY3VyZXBAMTE="

#lines = test.splitlines()
time_pattern = re.compile('(\d+\:\d+\:\d+\d+)')
ip_pattern = re.compile('(\d+\.\d+\.\d+\.\d+)')
s3 = boto3.client('s3')

#### IP regex ###
IPV4SEG  = r'(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
IPV4ADDR = r'(?:(?:' + IPV4SEG + r'\.){3,3}' + IPV4SEG + r')'
IPV6SEG  = r'(?:(?:[0-9a-fA-F]){1,4})'
IPV6GROUPS = (
    r'(?:' + IPV6SEG + r':){7,7}' + IPV6SEG,                  # 1:2:3:4:5:6:7:8
    r'(?:' + IPV6SEG + r':){1,7}:',                           # 1::                                 1:2:3:4:5:6:7::
    r'(?:' + IPV6SEG + r':){1,6}:' + IPV6SEG,                 # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
    r'(?:' + IPV6SEG + r':){1,5}(?::' + IPV6SEG + r'){1,2}',  # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
    r'(?:' + IPV6SEG + r':){1,4}(?::' + IPV6SEG + r'){1,3}',  # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
    r'(?:' + IPV6SEG + r':){1,3}(?::' + IPV6SEG + r'){1,4}',  # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
    r'(?:' + IPV6SEG + r':){1,2}(?::' + IPV6SEG + r'){1,5}',  # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
    IPV6SEG + r':(?:(?::' + IPV6SEG + r'){1,6})',             # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
    r':(?:(?::' + IPV6SEG + r'){1,7}|:)',                     # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
    r'fe80:(?::' + IPV6SEG + r'){0,4}%[0-9a-zA-Z]{1,}',       # fe80::7:8%eth0     fe80::7:8%1  (link-local IPv6 addresses with zone index)
    r'::(?:ffff(?::0{1,4}){0,1}:){0,1}[^\s:]' + IPV4ADDR,     # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255 (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
    r'(?:' + IPV6SEG + r':){1,4}:[^\s:]' + IPV4ADDR,          # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)
IPV6ADDR = '|'.join(['(?:{})'.format(g) for g in IPV6GROUPS[::-1]])

#######  EOM  ####     

def handler(event, context):
    for record in event['Records']:
        
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Get, read, and split the file into lines
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body'].read()
        lines = body.splitlines()
        #print (line)
        ###line = line.decode("utf-8")
        # date_p = date_p.search(line).group(1)
        # print (date_p)
        for line in lines:
            line = line.decode("utf-8")
            timestamp = time_pattern.search(line).group(1)
            if re.search(IPV4ADDR,line):
                ip= (re.search(IPV4ADDR,line).group())
            else:
                ip= (re.search(IPV6ADDR,line).group())
            method=(re.search("GET|POST|HEAD",line).group())
            
            key_pattern=(re.search(r'\b[0-9a-fA-F]{32}\b',line).group())
            date_p=(re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})',line).group())
            response_code=(re.search("200|302|304|403|400|404|409|500",line).group())
            name = (re.search((r'[A-Za-z]{2,25}( [A-Za-z]{2,25})?'),line).group())
            if re.search((r'(\b[0-1]+\.\d+\d+\b)'),line):
                response_time=(re.search((r'(\b[0-1]+\.\d+\d+\b)'),line).group())
            else:
                response_time= 0.0

            resources=re.findall(r'(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?', line)
            if re.search((r'[A-Za-z]{2,25}\s[A-Za-z]{2,25}'),line):
                device_name=(re.search((r'[A-Za-z]{2,25}\s[A-Za-z]{2,25}'),line).group())
            else:
                device_name ="unkown"
            
            #convert method
            response_time=float(response_time)
            response_code=int(response_code)


            data=json.dumps({"date":date_p+'T'+timestamp,"IP":ip,"method":method,"session_id":key_pattern,"response_code":response_code,"response_time":response_time,"Access_Resource":str(resources),"customer_name":name,"device_name":device_name})
            #print(data)
            resp = requests.post(url, headers=headers, data=data)
            #print(resp.status_code)

    print ("log files are pushed to ES ")
