import asyncio
import json
import urllib.request
import urllib.parse
import urllib.error

# 1. Login to get token
login_url = 'http://localhost:8004/api/v1/auth/login'
login_data = json.dumps({'email': 'admin@demo.com', 'password': 'password'}).encode('utf-8')
login_req = urllib.request.Request(login_url, data=login_data, headers={'Content-Type': 'application/json'}, method='POST')

try:
    with urllib.request.urlopen(login_req) as response:
        login_res = json.loads(response.read().decode('utf-8'))
        token = login_res['access_token']
except Exception as e:
    print("Login failed:", e)
    exit(1)

# 2. Call evidence search API with different methods
query = urllib.parse.quote('battery swelling')

for method in ['bm25', 'tfidf', 'dense', 'hybrid']:
    url = f'http://localhost:8004/api/v1/evidence/search?query={query}&method={method}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"Method: {method}")
            print("Result IDs:", [item['source_id'] for item in data['evidence']])
            print("-" * 20)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(e)
