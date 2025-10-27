import urllib.request
import ssl

proxy = 'http://brd-customer-hl_67f2d9ee-zone-residential_proxy1-country-il:vrqfz1kw74ec@brd.superproxy.io:33335'
url = 'https://geo.brdtest.com/mygeo.json'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
)

try:
    print(opener.open(url).read().decode())
except Exception as e:
    print(f"Error: {e}")
