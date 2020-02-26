import os
import requests
import yaml
import re
import json
from pathlib import Path

compiled_models = []
preserved_keys = ["config_url", "applications", "download_url", "name", "description", "cite", "authors", "documentation", "tags", "covers"]
assert 'url' not in preserved_keys

models_yaml_file = Path('src/manifest.model.yaml')
models_yaml = yaml.safe_load(models_yaml_file.read_text())

compiled_apps = {}
for k in models_yaml['applications']:
    app_url = models_yaml['applications'][k]
    if not app_url.startswith('http'):
        app_url = models_yaml['applications'][k].strip('/').strip('./')
        app_url = models_yaml['url_root'].strip('/') + '/' + app_url
    compiled_apps[k] = app_url

for item in models_yaml['models']:
    config_url = item['config_url']
    root_url = '/'.join(config_url.split('/')[:-1])
    response = requests.get(config_url)
    if response.status_code != 200:
        print('Failed to fetch model config from ' + config_url)
        continue

    model_config = yaml.safe_load(response.content)

    # merge item from models.yaml to model config
    model_config.update(item)
    model_info = {"root_url": root_url}
    for k in model_config:
        # normalize relative path
        if k in ['documentation']:
            model_config[k] = model_config[k].strip('/').strip('./')
        
        if k == 'covers':
            for j in range(len(model_config[k])):
                model_config[k][j] = model_config[k][j].strip('/').strip('./')

        if k in preserved_keys:
            model_info[k] = model_config[k]
            
    compiled_models.append(model_info)
    compiled_models.sort(key=lambda m: m['name'], reverse=True)

with open('manifest.model.json', 'wb') as f:
    models_yaml['models'] = compiled_models
    models_yaml['applications'] = compiled_apps
    f.write(json.dumps(models_yaml, indent=2, separators=(',', ': ')).encode('utf-8'))
