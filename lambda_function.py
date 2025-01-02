import os
import json
import urllib3
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

def lambda_handler(event, context):
    http = urllib3.PoolManager()
    base_url = "https://api.mobiwaternet.co.ke/"
    headers = {"Authorization": "Bearer " + os.environ["MOBI_BEARER_TOKEN"]}

    # print(event)
    # print(os.environ)

    if event['headers'].get("authorization") != "Bearer " + os.environ["DALGO_BEARER_TOKEN"]:
        return {
            'statusCode': 403,
            'body': 'unauthorized'
        }

    if event['rawPath'] == '/user-meter':
        r = http.request('GET', base_url + "monitoring/v1/flowdevices/flowDeviceAccess/", headers=headers)
        return {
            'statusCode': 200,
            'body': json.loads(r.data.decode('utf8'))
        }

    elif event['rawPath'] == '/meter-consumption':
        qs = event['rawQueryString']
        if qs:
            url_parameters = parse_qs(qs)
            if "flow_device_id" not in url_parameters:
                return {
                    "statusCode": 400,
                    "body": "missing parameter flow_device_id"
                }

            flow_device_id = url_parameters["flow_device_id"][0]

            if "fromDate" in url_parameters:
                from_date = url_parameters["fromDate"][0]
            else:
                from_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")

            if "toDate" in url_parameters:
                to_date = url_parameters['toDate'][0]
            else:
                to_date = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                
            url = base_url + f"monitoring/v1/flowdevices/flowDeviceAnalytics/consumption/{flow_device_id}?toDate={to_date}&fromDate={from_date}"
            print(url)
            r = http.request('GET', url, headers=headers)
            return {
                'statusCode': 200,
                'body': {"value": r.data.decode('utf8'), "flow_device_id": flow_device_id}
            }
