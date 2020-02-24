# Model repository for BioImage.io


## Models

* [RandomForestClassifierBroadNucleusDataBinarized](https://raw.githubusercontent.com/bioimage-io/python-bioimage-io/master/specs/models/sklearnbased/RandomForestClassifierBroadNucleusDataBinarized.model.yaml) [Ilastik]
* [UNet2DNucleiBroad](https://raw.githubusercontent.com/bioimage-io/pytorch-bioimage-io/master/specs/models/unet2d/nuclei_broad/UNet2DNucleiBroad.model.yaml) [Ilastik, ImJoy]

## How to contribute new models?
 1. Fork this repo
 1. Add your models to the `Models` section of README.md
 1. Run `python src/compile_list.py` to generate a new `manifest.model.json` with your models
 1. Commit your changes and send us a Pull Request.

