import requests

url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

payload={
  'scope': 'GIGACHAT_API_PERS'
}
headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Accept': 'application/json',
  'RqUID': 'dad38a1d-3dd5-470d-ab3a-cddb7ff2d13d',
  'Authorization': 'Basic MDE5YWY3ZDktNTc4OC03MjVkLTliMGMtOWFhY2IzOTk3OTU2OjNiZTVjZTU1LTIyYWUtNGU0Mi1hMGNkLTczODNmZTQ3NWExOQ=='
}

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

response = requests.request("POST", url, headers=headers, data=payload, verify=False)

print("Статус код:", response.status_code)
print("Ответ:")
print(response.text)