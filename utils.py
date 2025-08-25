from datetime import datetime
import pytz

def now_ams() -> str:
    tz = pytz.timezone("Europe/Amsterdam")
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M")
