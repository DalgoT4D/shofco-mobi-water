Background and Motivation
=========================

We invoke two APIs at Mobi's end:

(API-1)
https://api.mobiwaternet.co.ke/monitoring/v1/flowdevices/flowDeviceAccess/

which returns JSON, and then for each `flowDeviceId` in this response we invoke

(API-2)
https://api.mobiwaternet.co.ke/monitoring/v1/flowdevices/flowDeviceAnalytics/consumption/{flow_device_id}?toDate={to_date}&fromDate={from_date}

API-2 returns a number, but as text instead of in a JSON object. Airbyte can convert a plaintext response to JSON (https://docs.airbyte.com/connector-development/connector-builder-ui/record-processing#iterable) but only if the `Content-Type` is set to `text/plain` or `text/html`. Unfortunately Mobi's API returns a context type of `application/json` and so Airbyte does not do this.

Response formats
===============

API-1 returns a JSON object having the schema

```
flowDeviceName: string
flowDeviceLocation: string
flowDeviceDescription: string
flowDevicePulseRate: float
flowDeviceSize: float
deviceType: string
deviceId: integer
consumptionThreshold: float
organization:
  organizationId: integer
  organizationName: string
  organizationEmail: string
  organizationPhoneNo: string
  organizationCallbackUrl: string
flowDeviceId: integer
dailyConsumption: float
lastReceivedFlowData:
  measuredFlowRate: float
  predictedFlowRate: float
  acceptedFlowRate: float
  measuredConsumption: float
  predictedConsumption: float
  acceptedConsumption: float
  rawPulses: float
  measuredAt: string
  measuredFrom: string
  flowDeviceState: string
  notificationState: string
  flowDataId: integer
hardwareState: string
```

API-2 returns just text i.e.

```
r = requests.get("https://api.mobiwaternet.co.ke/monitoring/v1/flowdevices/flowDeviceAnalytics/consumption/268", 
                 params={"fromDate": "2024-01-01 00:00:00", "toDate": "2024-01-01 01:00:00"},
                 headers=headers)
# r.text == '0.0'
```

This number is the total water consumption over the queried time range.

Solution
========
Write a small API of our own (API-C) to wrap the response of the API-2 into a JSON object and call this from Airbyte's no-code connector. 

Airbyte's connector needs to 
1. Invoke API-1
2. Loop through the response
3. For each element, invoke API-2 on that `flowDeviceId`

Since each connector has only one base URL, our API-C wraps API-1 as well as API-2. The response from API-1 is forwarded as received, and the response from API-2 is wrapped into the object
`{"value": string, "flow_device_id": string, "date": date}`

Implementation
====================
A function on AWS Lambda, with an HTTP endpoint for invocation. The caller must pass a Bearer token to authenticate the request. The lambda compares this incoming token with the token saved in the environment variable `DALGO_BEARER_TOKEN`. The lambda then calls the Mobi API using the  `MOBI_BEARER_TOKEN`.

The lambda is invoked by sending a `POST` request to the endpoint `https://***********.lambda-url.ap-south-1.on.aws/` with the correct `Authorization` header. The response is always JSON.

Endpoint for API-1: `/user-meter`
Endpoint for API-2: `/meter-consumption?flow_device_id=XXX&startdate=XXX&tz=XXX`

We invoke API-2 one day at a time from the beginning of `startdate` to to the beginning of `today`. The timezone is computed using the `tz` parameter which is the timezone's IANA code.

The response is a list of values of the form
```
id: <primary key>
flow_device_id:
date: <yyyy-mm-dd>
value:
```


