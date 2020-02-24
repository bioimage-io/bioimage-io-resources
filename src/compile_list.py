import os
import requests
import yaml
import re
import json

models = []
preserved_keys = ["name", "description", "cite", "authors", "documentation", "tags"]
assert 'url' not in preserved_keys
with open('./README.md') as f:
    for line in f.readlines():
        if line.strip().startswith('*'):
            line = line.strip()
            temp = re.findall(r'[\(\[](.*?)[\)\]]', line)
            if len(temp) == 3:
                url = temp[1]
                response = requests.get(url)
                if response.status_code == 200:
                    model_yaml = yaml.safe_load(response.content)
                    model_info = {}
                    for k in model_yaml:
                        if k in preserved_keys:
                            model_info[k] = model_yaml[k]
                    if 'url' not in model_yaml:
                        model_info['url'] = url
                    else:
                        model_info['url'] = model_yaml['url']
                    models.append(model_info)
with open('src/manifest_template.json', 'rb') as t:
    template = json.loads(t.read())
    with open('manifest.model.json', 'wb') as f:
        template['models'] = models
        f.write(json.dumps(template, sort_keys=True, indent=2, separators=(',', ': ')).encode('utf-8'))