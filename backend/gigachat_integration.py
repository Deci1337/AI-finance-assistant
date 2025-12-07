import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MODEL = "GigaChat-Pro"

def get_access_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    payload = {'scope': 'GIGACHAT_API_PERS'}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'e1cda52c-b57a-477c-a65a-d9f896176e6d',
        'Authorization': 'Basic MDE5YWY3ZDktNTc4OC03MjVkLTliMGMtOWFhY2IzOTk3OTU2OjYzZTY1NTkzLTg3NDUtNGM1ZS05M2YwLTFlZDU1YTcwZGY1Mw=='
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

def get_models(access_token):
    url = "https://gigachat.devices.sberbank.ru/api/v1/models"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.request("GET", url, headers=headers, verify=False)
    return response.text

def chat_completion(access_token, message, model=MODEL):
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': message
            }
        ],
        'temperature': 0.7,
        'max_tokens': 1000
    }
    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': response.status_code, 'message': response.text}

if __name__ == "__main__":
    token = get_access_token()
    if token:
        print(f"Using model: {MODEL}\n")
        test_message = "Привет! Ты финансовый ассистент. Расскажи кратко о себе."
        print(f"Test message: {test_message}\n")
        result = chat_completion(token, test_message)
        if 'error' in result:
            print(f"Error: {result}")
        else:
            print("Response:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Failed to get access token")

