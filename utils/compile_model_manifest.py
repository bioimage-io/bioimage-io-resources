import os
import requests
import yaml
import re
import json
import traceback
import argparse
from pathlib import Path
from bioimageio.spec import __main__ as spec
from marshmallow import ValidationError

preserved_keys = [
    "api_version",
    "attachments",
    "authors",
    "badges",
    "cite",
    "co2",
    "covers",
    "description",
    "documentation",
    "download_url",
    "format_version",
    "git_repo",
    "icon",
    "id",
    "license",
    "links",
    "model",
    "name",
    "tags",
    "version",
    "error",
]
assert "url" not in preserved_keys

collections = []
compiled_apps = []
compiled_items = []


def parse_manifest(models_yaml):
    collection_tags = []
    if models_yaml.get("config"):
        cfg = models_yaml.get("config")
        if cfg.get("tags"):
            tags = cfg.get("tags")
            if isinstance(tags, list):
                collection_tags = cfg.get("tags")
    if "collection" in models_yaml:
        for item in models_yaml["collection"]:
            print("Loading collection from " + item["source"])
            response = requests.get(item["source"])
            if response.status_code != 200:
                print("Failed to fetch collection manifest from " + item["id"])
                continue
            collection_yaml = yaml.safe_load(response.content)
            collection_yaml["parent_collection"] = item["source"]
            if "config" in collection_yaml:
                collections.append(collection_yaml["config"])
            try:
                parse_manifest(collection_yaml)
            except Exception as e:
                print("Failed to parse manifest " + str(item.get("source")))
                print(traceback.format_exc())

    if "application" in models_yaml:
        for item in models_yaml["application"]:
            app_url = item.get("source")
            if not app_url:
                continue
            if app_url.endswith(".imjoy.html"):
                if os.path.exists(app_url):
                    content = open(app_url, "r").read()
                    if not app_url.startswith("http"):
                        app_url = item["source"].strip("/").strip("./")
                        app_url = (
                            models_yaml["config"]["url_root"].strip("/") + "/" + app_url
                        )
                else:

                    if not app_url.startswith("http"):
                        app_url = item["source"].strip("/").strip("./")
                        app_url = (
                            models_yaml["config"]["url_root"].strip("/") + "/" + app_url
                        )

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

                app_config = {
                    "id": item["id"],
                    "type": "application",
                    "source": app_url,
                    "passive": item.get("passive", False),
                }
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
                    "passive",
                ]
                for f in fields:
                    if f in plugin_config:
                        app_config[f] = plugin_config[f]
                tags = plugin_config.get("labels", []) + plugin_config.get("flags", [])
                app_config["tags"] = tags
                app_config["documentation"] = plugin_config.get("docs")
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
            else:
                item["type"] = "application"
                app_config = item
            if "id" not in app_config:
                app_config["id"] = app_config["name"].replace(" ", "-")
            app_config["id"] = models_yaml["config"]["id"] + "/" + app_config["id"]
            if "links" in app_config:
                for i in range(len(app_config["links"])):
                    if "/" not in app_config["links"][i]:
                        app_config["links"][i] = (
                            models_yaml["config"]["id"] + "/" + app_config["links"][i]
                        )

            compiled_apps.append(app_config)
            print("Added application: " + app_config["name"])

    for tp in ["model", "dataset", "notebook", "workflow"]:
        if tp not in models_yaml:
            continue
        for item in models_yaml[tp]:
            model_info = {"type": tp, "attachments": {}}
            if "source" in item and (
                item["source"].endswith("yaml") or item["source"].endswith("yml")
            ):
                source = item["source"]

                try:
                    if source.startswith("http"):
                        response = requests.get(source)
                        if response.status_code != 200:
                            print("Failed to fetch source from " + source)
                            continue
                        if source.endswith(".yaml") or source.endswith(".yml"):
                            model_config = yaml.safe_load(response.content)
                        root_url = "/".join(source.split("/")[:-1])
                    else:
                        with open(source, "rb") as fil:
                            model_config = yaml.safe_load(fil)
                        item["source"] = (
                            models_yaml["config"]["url_root"].strip("/") + "/" + source
                        )
                        root_url = (
                            models_yaml["config"]["url_root"].strip("/")
                            + "/"
                            + "/".join(source.split("/")[:-1])
                        )
                    # merge item from models.yaml to model config
                    item.update(model_config)
                    if tp == "model":
                        if "error" not in item:
                            item["error"] = {}
                        try:
                            spec.verify_model_data(model_config)
                        except ValidationError as e:
                            print(f'Error when verifying {item["id"]}: {e.messages}')
                            item["error"] = {"spec": e.messages}
                        except Exception as e:
                            print(f'Failed to verify the model: {item["id"]}: {e}')
                            item["error"] = {"spec": f"Failed to verify the model: {e}"}
                except:
                    print("Failed to download or parse source file from " + source)
                    raise
                model_info['source'] = source
            else:
                root_url = None
            
            if root_url is not None:
                model_info["root_url"] = root_url
            attachments = model_info["attachments"]
            if "files" in item:
                attachments["files"] = item["files"]
            if "weights" in item:
                attachments["weights"] = item["weights"]
            for k in item:
                # normalize relative path
                if k in ["documentation"]:
                    if item[k]:
                        item[k] = item[k].strip("/").strip("./")

                if k == "covers":
                    if isinstance(item[k], list):
                        for j in range(len(item[k])):
                            item[k][j] = item[k][j].strip("/").strip("./")

                if k in preserved_keys: # don't copy model source
                    model_info[k] = item[k]
            if 'source' not in model_info and 'source' in item:
                model_info['source'] = item['source']

            if len(model_info["attachments"]) <= 0:
                del model_info["attachments"]

            if "tags" in model_info:
                model_info["tags"] += collection_tags
            else:
                model_info["tags"] = collection_tags
            if "id" not in model_info:
                model_info["id"] = model_info["name"].replace(" ", "-")
            model_info["id"] = models_yaml["config"]["id"] + "/" + model_info["id"]
            if "links" in model_info:
                for i in range(len(model_info["links"])):
                    if "/" not in model_info["links"][i]:
                        model_info["links"][i] = (
                            models_yaml["config"]["id"] + "/" + model_info["links"][i]
                        )

            compiled_items.append(model_info)
            print("Added " + model_info["type"] + ": " + model_info["name"])


parser = argparse.ArgumentParser()
parser.add_argument(
    "--manifest",
    type=str,
    default="manifest.bioimage.io.yaml",
    help="Path to the input manifest yaml file",
)
parser.add_argument(
    "--output",
    type=str,
    default="manifest.bioimage.io.json",
    help="Output file path for the compiled json file",
)
args = parser.parse_args()

models_yaml_file = Path(args.manifest)
models_yaml = yaml.safe_load(models_yaml_file.read_text())
parse_manifest(models_yaml)

with Path(args.output).open("wb") as f:
    new_model_yaml = models_yaml["config"]
    collections.sort(key=lambda m: m["name"], reverse=True)
    compiled_apps.sort(key=lambda m: m["name"], reverse=True)
    compiled_items.sort(key=lambda m: m["name"], reverse=True)
    new_model_yaml["collections"] = collections
    resources = compiled_apps + compiled_items
    unique_res = {}
    duplicated = []
    for res in resources:
        if "tags" in res:
            res["tags"] = list(set(res["tags"]))
        if res["id"] in unique_res:
            old = unique_res[res["id"]]
            for k in old:
                if old[k] != res[k]:
                    raise Exception("Duplicated resource id found: " + res["id"])
            for k in res:
                if old[k] != res[k]:
                    raise Exception("Duplicated resource id found: " + res["id"])
            duplicated.append(res)

        unique_res[res["id"]] = res
    for res in duplicated:
        print("Removing duplicated item: " + res["name"])
        resources.remove(res)
    new_model_yaml["resources"] = resources
    print("Done! Successfully added " + str(len(resources)) + " items.")
    f.write(
        json.dumps(new_model_yaml, indent=2, separators=(",", ": ")).encode("utf-8")
    )
