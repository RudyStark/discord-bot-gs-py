import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GS_CHANNEL_ID = int(os.getenv('CHANNEL_ID'))