import os
import time
import http.client
import json
import logging
from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

logging_levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


logging.basicConfig(level=logging_levels[os.environ.get('LOGGING_LEVEL', 'info')])
load_dotenv('secret.env')


TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "your_chat_id")
TELEGRAM_API_URL = f"api.telegram.org"

influx_configuration = {
    "influxdb_url": os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
    "influxdb_token": os.environ.get("INFLUXDB_TOKEN", None),
    "influxdb_org": os.environ.get("INFLUXDB_ORG", "sample"),
    "influxdb_bucket": os.environ.get("INFLUXDB_BUCKET", "mqtt"),
}

config_json = json.dumps(influx_configuration, indent=4)
logging.debug(f'Influx config: {config_json}')


client = InfluxDBClient(
    url=influx_configuration["influxdb_url"],
    token=influx_configuration["influxdb_token"],
    org=influx_configuration["influxdb_org"]
)

query_api = client.query_api()


def send_telegram_message(num_events):
    if num_events > 0:
        message = (f'Количество срабатываний датчика движений {num_events}, '
                   f'в кабинете кто-то есть, можно не брать ключи. ✅')
    else:
        message = (f'Количество срабатываний датчика движений {num_events}, '
                   f'похоже что никого в кабинете нет, нужно взять ключи на вахте. ❌')
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    headers = {"Content-Type": "application/json"}
    conn = http.client.HTTPSConnection(TELEGRAM_API_URL)

    # Send POST request
    conn.request("POST", f"/bot{TELEGRAM_BOT_TOKEN}/sendMessage", body=json.dumps(data), headers=headers)

    response = conn.getresponse()
    response_data = response.read().decode()

    if response.status == 200:
        logging.info('Message sent successfully.')
    else:
        logging.info('Failed to send message.')
        logging.debug(f'Status code: {response.status}, Response: {response_data}')


def check_occupancy_events():
    now = datetime.utcnow()
    start_time = now - timedelta(minutes=60)
    logging.debug(f'time range is: {start_time}, end time is: {now.isoformat()}')

    query = f'''
    from(bucket: "{influx_configuration["influxdb_bucket"]}")
      |> range(start: {start_time.isoformat()}Z, stop: {now.isoformat()}Z)
      |> filter(fn: (r) => r["_measurement"] == "zigbee2mqtt/motion-sensor-01" and r["_field"] == "occupancy")
      |> aggregateWindow(every: 1m, fn: count)
      |> yield(name: "count")
    '''

    result = query_api.query(org=influx_configuration["influxdb_org"], query=query)

    event_count = 0
    for table in result:
        for record in table.records:
            event_count += record.get_value()

    logging.info(f'Trying to send message. Event count is {event_count}.')
    send_telegram_message(event_count)


if __name__ == "__main__":
    check_occupancy_events()
