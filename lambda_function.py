import os
import json
import urllib3
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import dateutil.tz

def validate_timezone(tz_name):
    return dateutil.tz.gettz(tz_name)

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

            if "startdate" not in url_parameters:
                return {
                    "statusCode": 400,
                    "body": "missing parameter startdate"
                }

            if "tz" not in url_parameters:
                return {
                    "statusCode": 400,
                    "body": "missing parameter tz"
                }

            flow_device_id = url_parameters["flow_device_id"][0]
            startdate_str = url_parameters["startdate"][0]
            iana_tz = url_parameters["tz"][0]

            # print(flow_device_id)
            # print(startdate_str)
            # print(iana_tz)

            tz = validate_timezone(iana_tz)
            if tz is None:
                return {
                    "statusCode": 400,
                    "body": "invalid timezone parameter " + iana_tz
                }


            retval = []
            startdate = datetime.strptime(startdate_str, "%Y-%m-%d").replace(tzinfo=tz)
            enddate = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)

            dtiter = startdate
            while dtiter < enddate:
                q_sdate = dtiter.strftime("%Y-%m-%d %H:%M:%S")
                q_edate = (dtiter + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")                
                url = base_url + f"monitoring/v1/flowdevices/flowDeviceAnalytics/consumption/{flow_device_id}?toDate={q_edate}&fromDate={q_sdate}"
                # print(url)
                r = http.request('GET', url, headers=headers)
                retval.append({
                    "flow_device_id": flow_device_id,
                    "date": dtiter.strftime("%Y-%m-%d"),
                    "value": r.data.decode('utf8')
                })
                dtiter += timedelta(days=1)
                # print(dtiter.strftime("%Y-%m-%d") + "    " + enddate.strftime("%Y-%m-%d"))
            return {
                'statusCode': 200,
                'body': retval
            }
        else:
            return {
                "statusCode": 400,
                "body": "missing query parameters"
            }
    else:
        return {
            "statusCode": 400,
            "body": "unknown endpoint " + event['rawPath']
        }
