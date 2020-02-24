import os
import requests
import yaml
import re
import json

compiled_models = []
preserved_keys = ["config_url", "applications", "download_url", "name", "description", "cite", "authors", "documentation", "tags", "covers"]
assert 'url' not in preserved_keys
with open('./src/models.yaml') as f:
    model_list = yaml.safe_load(f.read())
    for item in model_list:
        config_url = item['config_url']
        root_url = '/'.join(config_url.split('/')[:-1])
        response = requests.get(config_url)
        if response.status_code == 200:
            model_config = yaml.safe_load(response.content)

            # merge item from models.yaml to model config
            model_config.update(item)
            model_info = {"root_url": root_url}
            for k in model_config:
                if k == 'config_url':
                    model_config[k] = config_url.split('/')[-1]
                # normalize relative path
                if k in ['documentation']:
                    model_config[k] = model_config[k].strip('/').strip('./')
                
                if k == 'covers':
                    for j in model_config[k]:
                        model_config[k][j] = model_config[k][j].strip('/').strip('./')

                if k in preserved_keys:
                    model_info[k] = model_config[k]
                
            compiled_models.append(model_info)

with open('src/manifest_template.json', 'rb') as t:
    template = json.loads(t.read())
    with open('manifest.model.json', 'wb') as f:
        template['models'] = compiled_models
        f.write(json.dumps(template, sort_keys=True, indent=2, separators=(',', ': ')).encode('utf-8'))
