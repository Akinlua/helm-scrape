import urllib.request
import ssl

proxy = 'http://brd-customer-hl_2bff2960-zone-residential_proxy1-country-il:g3v45vaqd4iz@brd.superproxy.io:33335'
url = ' https://geo.brdtest.com/mygeo.json'

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
    urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
)

try:
    print(opener.open(url).read().decode())
except Exception as e:
    print(f"Error: {e}")
