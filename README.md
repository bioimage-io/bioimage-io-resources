[![Gitter](https://badges.gitter.im/bioimage-io/community.svg)](https://gitter.im/bioimage-io/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)

# Model repository for BioImage.io


## Models

A list of models can be found [here](manifest.bioimage.io.yaml).

## How to contribute?

You are welcome to submit your models (together with datasets, applications and Jupyter notebooks) to the model repository, please follow the guideline [here](https://bioimage.io/#/?show=contribute).

## How integrate the model zoo to my own software?

If you are developing or maintaining a software which can digest models in the model description format used in the BioImage model zoo, it's easy to fetch the latest model list (along with the other meta information) from this url `https://bioimage-io.github.io/bioimage-io-models/manifest.bioimage.io.json`. 

By fetching the content of this JSON file, you will get all the models from the BioImage model zoo, and you can filter it based on your own supported framework, programming language etc.