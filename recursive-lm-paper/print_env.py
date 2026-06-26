import os
for k, v in os.environ.items():
    if "KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper() or "PASS" in k.upper() or "API" in k.upper():
        print(k, "is present")
