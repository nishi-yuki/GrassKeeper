from datetime import datetime, date, time, timezone, timedelta
import os
import json
import requests
import traceback
import textwrap


APP_NAME = 'grasskeeper'
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
          }
        }
      }
    }
    '''
    graphql_error_key = 'errors'

    def __init__(self, token, username):
        self.headers = {'Authorization': 'bearer ' + token}
        self.username = username

    def fetch_grass_info(self, fromdate, todate):
        variables = {'userName': self.username, 'from': fromdate, 'to': todate}
        variables = json.dumps(variables)
        payload = {'query': self.query, 'variables': variables}

        res = requests.post(self.endpoint, headers=self.headers,
                            data=json.dumps(payload))
        if res.status_code != 200:
            raise Exception(res.status_code, res.text)

        res_json = res.json()

        if self.graphql_error_key in res_json: # GraphQL error
            raise Exception(res_json[self.graphql_error_key])
        return res_json

    def fetch_grass_total(self, fromdate, todate):
        res = self.fetch_grass_info(fromdate, todate)
        c = res['data']['user']['contributionsCollection']
        return c['contributionCalendar']['totalContributions']


def calc_day_start_and_end(day: date, tzinfo):
    day_start = datetime.combine(day, time.min, tzinfo=tzinfo)
    day_start = day_start.isoformat()
    day_end = datetime.combine(day, time.max, tzinfo=tzinfo)
    day_end = day_end.isoformat()
    return day_start, day_end


class DiscordWebhookClient:
    endpoint = 'https://discord.com/api/webhooks/{webhook_id}/{webhook_token}'

    def __init__(self, webhook_id, webhook_token):
        self.endpoint = self.endpoint.format(
            webhook_id=webhook_id, webhook_token=webhook_token)

    def send(self, content):
        headers = {'Content-Type': 'application/json'}
        payload = {'content': content}
        res = requests.post(
            self.endpoint, headers=headers, data=json.dumps(payload))
        if res.status_code != 204:
            raise Exception('Failed to send message')


class ErrorNotifier:
    def __init__(self, notifier):
        self.notifier = notifier

    def send_exception(self, e):
        f = '''
        **[{}] エラーが発生しました**
        `{}`
        ```{}```
        '''
        f = textwrap.dedent(f[1:-1])
        content = f.format(APP_NAME, repr(e), traceback.format_exc())
        print(content)
        self.notifier.send(content)


def main():
    ENV = os.environ.get('ENV', 'dev').lower()

    token = os.environ['GITHUB_TOKEN']
    username = os.environ['GITHUB_USERNAME']
    github_client = GithubApiClient(token, username)

    webhook_id = os.environ['DISCORD_WEBHOOK_ID']
    webhook_token = os.environ['DISCORD_WEBHOOK_TOKEN']
    discord_client = DiscordWebhookClient(webhook_id, webhook_token)

    error_notifier = ErrorNotifier(discord_client)

    today = datetime.now(tz=TZ_INFO).date()
    start, end = calc_day_start_and_end(day=today, tzinfo=TZ_INFO)
    print(f'[*] Fetching grass info from {start} to {end}')

    try:
        grass_info = github_client.fetch_grass_total(start, end)
    except Exception as e:
        error_notifier.send_exception(e)
        raise e
    print(f'[*] grass_info: {grass_info}')

    if ENV == 'dev':
        discord_client.send(f'[*] grass_info: {grass_info}')

    if grass_info == 0:
        discord_client.send('今日はまだ草生やしてないよ')


def handler(event, context):
    main()


if __name__ == '__main__':
    read_env()
    main()
