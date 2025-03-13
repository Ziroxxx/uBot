import json

config_path = "/opt/uBot/config/conf.json"

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

BOT_TOKEN = config.get('telegram_token')
PSQL_DB_NAME = config.get('psqlDbName')
PSQL_USER = config.get('postgres')
PSQL_HOST = config.get("psqlHost")
PSQL_PORT = config.get('psqlPort')
PSQL_PASSWORD = config.get('psqlPassword')
TIME_FOR_ACCEPT_IN_MINUTES = config.get('time_to_accept_in_minutes')
TIME_FOR_DONE_IN_MINUTES = config.get('time_to_done_in_minutes')