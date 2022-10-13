from datetime import datetime, date, time, timezone, timedelta
import os
import json
import requests


TZ_INFO = timezone(timedelta(hours=9))


def read_env():
    with open('.env', 'rt') as f:
        for l in f.readlines():
            key, value = l.split('=')
            value = value.strip()
            value = value.strip('\'"')
            os.environ[key] = value


class GithubApiClient:
    endpoint = 'https://api.github.com/graphql'
    query = '''
    query($userName:String!, $from:DateTime!, $to:DateTime!) {
      user(login: $userName){
        contributionsCollection (from: $from, to: $to) {
          contributionCalendar {
            totalContributions
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

    def __init__(self, token, username):
        self.headers = {'Authorization': 'bearer ' + token}
        self.username = username

    def fetch_grass_info(self, fromdate, todate):
        variables = {'userName': username, 'from': fromdate, 'to': todate}
        variables = json.dumps(variables)
        payload = {'query': self.query, 'variables': variables}

        res = requests.post(self.endpoint, headers=self.headers,
                            data=json.dumps(payload))
        res = res.json()
        # print(json.dumps(res, indent=2))
        return res

    def fetch_grass_total(self, fromdate, todate):
        res = self.fetch_grass_info(fromdate, todate)
        c = res['data']['user']['contributionsCollection']
        return c['contributionCalendar']['totalContributions']


def calc_today_start_and_end():
    today = date.today()
    today_start = datetime.combine(today, time.min, tzinfo=TZ_INFO)
    today_start = today_start.isoformat()
    today_end = datetime.combine(today, time.max, tzinfo=TZ_INFO)
    today_end = today_end.isoformat()
    return today_start, today_end


if __name__ == '__main__':
    read_env()
    token = os.environ['GITHUB_TOKEN']
    username = os.environ['GITHUB_USERNAME']
    start, end = calc_today_start_and_end()

    client = GithubApiClient(token, username)
    grass_info = client.fetch_grass_total(start, end)
    print(grass_info)
