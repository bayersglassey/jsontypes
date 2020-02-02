import os
import json

from jsontypes import JsonType

hr = "-" * 30

for filename in os.listdir("examples"):
    if not filename.endswith(".json"): continue
    print(hr)
    print("Example: {}".format(filename))
    print(hr)
    data = json.load(open(os.path.join("examples", filename)))
    j = JsonType(data)
    j.show()
    print()
