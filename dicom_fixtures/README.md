# dicom-fixtures

Dicom-fixtures is a python library for generating DICOM files represented by a `pydicom.Dataset`.
This library can be used to generate testing data for applications dealing with medical imagery.

## Usage

```python
import dicom_fixtures

# Create a dummy image
ds = dicom_fixtures.ImageFactory()

# Create an image using a custom filepath
ds = dicom_fixtures.ImageFactory(image_path="meme.png")
```
