from datetime import datetime, date, time, timezone, timedelta
import os
import json
import requests

ENDPOINT = 'https://api.github.com/graphql'
TZ_INFO = timezone(timedelta(hours=9))

with open('.env', 'rt') as f:
    for l in f.readlines():
        key, value = l.split('=')
        value = value.strip()
        value = value.strip('\'"')
        os.environ[key] = value

token = os.environ['GITHUB_TOKEN']
username = os.environ['GITHUB_USERNAME']

headers = {'Authorization': 'bearer ' + token}

query = '''
query($userName:String!, $from:DateTime!, $to:DateTime!) {
  user(login: $userName){
    contributionsCollection (from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
'''


today = date.today()
today_start = datetime.combine(today, time.min, tzinfo=TZ_INFO)
today_start = today_start.isoformat()
today_end = datetime.combine(today, time.max, tzinfo=TZ_INFO)
today_end = today_end.isoformat()

variables = {'userName': username, 'from': today_start, 'to': today_end}
variables = json.dumps(variables)

print(variables)


payload = {'query': query, 'variables': variables}

res = requests.post(ENDPOINT, headers=headers, data=json.dumps(payload))
res = res.json()

print(json.dumps(res, indent=2))
