
import requests
from jsontypes import JsonType

URL = "https://api.github.com/events"

resp = requests.get(URL)
events = resp.json()

jt = JsonType(*events)
jt.show()
