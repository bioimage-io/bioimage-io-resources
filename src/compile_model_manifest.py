import os
import requests
import yaml
import re
import json
from pathlib import Path

preserved_keys = [
    "api_version",
    "authors",
    "git_repo",
    "cite",
    "co2",
    "covers",
    "badges",
    "description",
    "documentation",
    "download_url",
    "attachments",
    "format_version",
    "id",
    "license",
    "model",
    "name",
    "source",
    "tags",
    "version",
    "links",
    "icon",
]
assert "url" not in preserved_keys

collections = []
compiled_apps = []
apps_names = []
compiled_items = []


def parse_manifest(models_yaml):
    if "collection" in models_yaml:
        for item in models_yaml["collection"]:
            response = requests.get(item["source"])
            if response.status_code != 200:
                print("Failed to fetch collection manifest from " + item["id"])
                continue
            collection_yaml = yaml.safe_load(response.content)
            if "config" in collection_yaml:
                collections.append(collection_yaml["config"])
            # TODO: add tags automatically
            parse_manifest(collection_yaml)

    if "application" in models_yaml:
        for item in models_yaml["application"]:
            app_url = item["source"]
            if os.path.exists(app_url):
                content = open(app_url, "r").read()
                if not app_url.startswith("http"):
                    app_url = item["source"].strip("/").strip("./")
                    app_url = models_yaml["url_root"].strip("/") + "/" + app_url
            else:
                if not app_url.startswith("http"):
                    app_url = item["source"].strip("/").strip("./")
                    app_url = models_yaml["url_root"].strip("/") + "/" + app_url

                response = requests.get(app_url)
                if response.status_code != 200:
                    print("Failed to fetch model config from " + app_url)
                    continue

                content = response.content.decode("utf-8")
            found = re.findall("<config (.*)>(.*)</config>", content, re.DOTALL)[0]
            if "json" in found[0]:
                plugin_config = json.loads(found[1])
            elif "yaml" in found[0]:
                plugin_config = yaml.safe_load(found[1])
            else:
                raise Exception("config not found in " + app_url)

            app_config = {"id": item["id"], "type": "application", "source": app_url}
            fields = [
                "icon",
                "name",
                "version",
                "api_version",
                "description",
                "license",
                "requirements",
                "dependencies",
                "env",
            ]
            for f in fields:
                if f in plugin_config:
                    app_config[f] = plugin_config[f]
            tags = plugin_config.get("labels", []) + plugin_config.get("flags", [])
            app_config["tags"] = tags

            app_config["covers"] = plugin_config.get("cover")
            # make sure we have a list
            if not app_config["covers"]:
                app_config["covers"] = []
            elif type(app_config["covers"]) is not list:
                app_config["covers"] = [app_config["covers"]]

            app_config["badges"] = plugin_config.get("badge")
            if not app_config["badges"]:
                app_config["badges"] = []
            elif type(app_config["badges"]) is not list:
                app_config["badges"] = [app_config["badges"]]

            app_config["authors"] = plugin_config.get("author")
            if not app_config["authors"]:
                app_config["authors"] = []
            elif type(app_config["authors"]) is not list:
                app_config["authors"] = [app_config["authors"]]

            assert item["id"] == plugin_config["name"], (
                "Please use the app name ("
                + plugin_config["name"]
                + ") as its application id."
            )
            apps_names.append(plugin_config["name"])
            compiled_apps.append(app_config)

    for tp in ["model", "dataset", "notebook"]:
        if tp not in models_yaml:
            continue
        for item in models_yaml[tp]:
            source = item["source"]
            root_url = "/".join(source.split("/")[:-1])
            response = requests.get(source)
            if response.status_code != 200:
                print("Failed to fetch source from " + source)
                continue

            model_config = yaml.safe_load(response.content)

            # merge item from models.yaml to model config
            model_config.update(item)
            model_info = {"root_url": root_url, "type": tp, "attachments": {}}
            attachments = model_info["attachments"]
            if "files" in model_config:
                attachments["files"] = model_config["files"]
            if "weights" in model_config:
                attachments["weights"] = model_config["weights"]
            for k in model_config:
                # normalize relative path
                if k in ["documentation"]:
                    if model_config[k]:
                        model_config[k] = model_config[k].strip("/").strip("./")

                if k == "covers":
                    for j in range(len(model_config[k])):
                        model_config[k][j] = model_config[k][j].strip("/").strip("./")

                if k in preserved_keys:
                    model_info[k] = model_config[k]

            if len(model_info["attachments"]) <= 0:
                del model_info["attachments"]

            compiled_items.append(model_info)


models_yaml_file = Path(__file__).parent / "manifest.bioimage.io.yaml"
models_yaml = yaml.safe_load(models_yaml_file.read_text())
parse_manifest(models_yaml)

with (Path(__file__).parent / "../manifest.bioimage.io.json").open("wb") as f:
    new_model_yaml = {
        "name": models_yaml["name"],
        "description": models_yaml["description"],
        "version": models_yaml["version"],
        "url_root": models_yaml["url_root"],
    }
    collections.sort(key=lambda m: m["name"], reverse=True)
    compiled_apps.sort(key=lambda m: m["name"], reverse=True)
    compiled_items.sort(key=lambda m: m["name"], reverse=True)
    new_model_yaml["collections"] = collections
    resources = compiled_apps + compiled_items
    ids = []
    for res in resources:
        if 'id' not in res:
            res['id'] = res['name'].replace(' ', '-')
        if res['id'] in ids:
            raise Exception("Duplicated resource id found: " + res['id'])
        ids.append(res['id'])

    new_model_yaml["resources"] = resources
    f.write(
        json.dumps(new_model_yaml, indent=2, separators=(",", ": ")).encode("utf-8")
    )
