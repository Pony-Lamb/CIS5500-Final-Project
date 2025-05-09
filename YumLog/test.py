import requests

url = 'http://127.0.0.1:8000/smart_recs?page=9000'

response = requests.get(url)
response_time = response.elapsed.total_seconds()

print('Time consumed to respond to user request: ' + str(response_time) + ' s')