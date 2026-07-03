#!/usr/bin/env python3
"""Add CodeBuddy LLM model to AWS E2E Demo team (mirrored from Build System)"""
import urllib.request, json, http.cookiejar, sys

BASE = 'http://127.0.0.1:8080/api/v1'
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# 1. Register
try:
    reg = opener.open(urllib.request.Request(f'{BASE}/auth/register',
        data=json.dumps({'username':f'e2e_addllm', 'password':'e2e_addllm'}).encode(),
        headers={'Content-Type':'application/json'}, method='POST'))
    auth = json.load(reg)
    csrf = auth.get('csrf_token','')
    print(f'✅ Registration OK, csrf={csrf[:16]}...')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'❌ Register failed: {e.code} {body}')
    # Try login
    try:
        login = opener.open(urllib.request.Request(f'{BASE}/auth/login',
            data=json.dumps({'username':'e2e_addllm', 'password':'e2e_addllm'}).encode(),
            headers={'Content-Type':'application/json'}, method='POST'))
        auth = json.load(login)
        csrf = auth.get('csrf_token','')
        print(f'✅ Login OK, csrf={csrf[:16]}...')
    except Exception as e2:
        print(f'❌ Login also failed: {e2}')
        sys.exit(1)

# 2. Get Build System codebuddy model from list
try:
    r = opener.open(urllib.request.Request(f'{BASE}/agent-config/teams/build_system/models'))
    models_list = json.load(r)
    items = models_list if isinstance(models_list, list) else models_list.get('models', models_list.get('items', []))
    model = next((m for m in items if m.get('model_id') == 'codebuddy' or 'codebuddy' in str(m.get('name','')).lower()), None)
    if not model and items:
        model = items[0]  # fallback
    if not model:
        print('❌ No codebuddy model found in Build System')
        sys.exit(1)
    has_key = bool(model.get('api_key',''))
    print(f'✅ Build System codebuddy: provider={model.get("provider")} has_api_key={has_key}')
except Exception as e:
    print(f'❌ Cannot read Build System models: {e}')
    sys.exit(1)

# 3. Add to AWS team
payload = {
    'provider': model.get('provider','deepseek'),
    'name': model.get('name','deepseek-v4-pro'),
    'max_tokens': int(model.get('max_tokens',4096)),
    'temperature': float(model.get('temperature',0.7)),
    'is_default': True,
    'api_key': model.get('api_key',''),
    'api_base_url': model.get('api_base_url','https://api.deepseek.com'),
}
try:
    create_req = urllib.request.Request(
        f'{BASE}/agent-config/teams/a7c36670/models',
        data=json.dumps(payload).encode(),
        headers={'Content-Type':'application/json','x-csrf-token':csrf},
        method='POST'
    )
    result = json.load(opener.open(create_req))
    print(f'✅ Model added! id={result.get("model_id","?")} default={result.get("is_default","?")}')
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'❌ Add failed HTTP {e.code}: {body[:300]}')
    
    # Try without api_base_url
    if 'api_base_url' in body.lower() or e.code == 400:
        payload2 = {k:v for k,v in payload.items() if k != 'api_base_url'}
        try:
            create_req2 = urllib.request.Request(
                f'{BASE}/agent-config/teams/a7c36670/models',
                data=json.dumps(payload2).encode(),
                headers={'Content-Type':'application/json','x-csrf-token':csrf},
                method='POST'
            )
            result2 = json.load(opener.open(create_req2))
            print(f'✅ Model added (no base_url)! id={result2.get("model_id","?")}')
        except Exception as e2:
            print(f'❌ Fallback also failed: {e2}')
