import glob
import os
import string
from dataclasses import dataclass
from datetime import datetime
from hashlib import md5
from random import randint

import factory
import numpy as np
import pydicom
from faker import Faker
from PIL import Image

dir_path = os.path.dirname(os.path.realpath(__file__))
img_dir = os.path.join(dir_path, "images")
faker = Faker()


def uid() -> str:
    # TODO: How to create a great UID function to minimize collisions?
    return f"1.3.6.4.1.58139{randint(100000,99999999)}"


class ImageFactory(factory.Factory):
    class Meta:
        model = pydicom.Dataset
        strategy = factory.BUILD_STRATEGY

    image_path = factory.Iterator(glob.glob(img_dir + "/*"))

    # DICOM Attrs
    PatientID = factory.LazyFunction(
        lambda: "".join(string.ascii_lowercase[randint(0, 25)] for _ in range(10))
    )
    PatientName = factory.LazyAttribute(lambda _: faker.name())
    AccessionNumber = factory.LazyAttribute(lambda _: faker.md5(raw_output=False))
    SOPInstanceUID = factory.LazyFunction(uid)
    SeriesInstanceUID = factory.LazyFunction(uid)
    StudyInstanceUID = factory.LazyFunction(uid)
    SOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    PatientSex = "F"
    PatientBirthDate = "19000101"
    StudyID = "1"
    SeriesNumber = "2"
    InstanceNumber = "3"
    StudyTime = "000000.000000"
    Laterality = "R"
    Modality = ""

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        d = model_class()
        for k, v in kwargs.items():
            if k not in set(["image_path"]):
                setattr(d, k, v)

        file = kwargs.get("image_path")
        if file:
            im_frame = Image.open(file)
            if im_frame.mode == "L":
                # (8-bit pixels, black and white)
                np_frame = np.array(im_frame.getdata(), dtype=np.uint8)
                d.Rows = im_frame.height
                d.Columns = im_frame.width
                d.PhotometricInterpretation = "MONOCHROME1"
                d.SamplesPerPixel = 1
                d.BitsStored = 8
                d.BitsAllocated = 8
                d.HighBit = 7
                d.PixelRepresentation = 0
                d.PixelData = np_frame.tobytes()
            elif im_frame.mode == "RGBA" or im_frame.mode == "RGB":
                if im_frame.mode == "RGBA":
                    np_frame = np.array(im_frame.getdata(), dtype=np.uint8)[:, :3]
                elif im_frame.mode == "RGB":
                    np_frame = np.array(im_frame.getdata(), dtype=np.uint8)
                d.Rows = im_frame.height
                d.Columns = im_frame.width
                d.PhotometricInterpretation = "RGB"
                d.SamplesPerPixel = 3
                d.BitsStored = 8
                d.BitsAllocated = 8
                d.HighBit = 7
                d.PixelRepresentation = 0
                d.PlanarConfiguration = 0
                d.PixelData = np_frame.tobytes()
            else:
                print("NOT SETTING PIXEL DATA")
        d.file_meta = pydicom.Dataset()
        d.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
        d.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
        d.file_meta.ImplementationVersionName = "DCARDOZA"
        d.file_meta.ImplementationClassUID = "1.3.6.1.4.1.58139"
        d.file_meta.SourceApplicationEntityTitle = "DICOM_FIXTURES"
        d.is_implicit_vr = True
        d.is_little_endian = True
        return d


@dataclass
class Exam:
    num_images: int = 0
    images: list = None
    image_dir: str = ""
    image_paths: list = None

    image_attrs: dict = None
    images: list = None


class ExamFactory(factory.Factory):
    class Meta:
        model = Exam
        strategy = factory.BUILD_STRATEGY

    num_images = 4
    image_dir = img_dir
    image_paths = factory.LazyAttribute(lambda o: glob.glob(o.image_dir + "/*"))

    default_image_attrs = factory.Dict(
        {
            "PatientID": factory.LazyAttribute(lambda _: faker.md5(raw_output=False)),
            "PatientName": factory.LazyAttribute(lambda _: faker.name()),
            "PatientBirthDate": factory.LazyAttribute(
                lambda _: faker.date_of_birth(minimum_age=45, maximum_age=90).strftime("%Y%m%d")
            ),
            "AccessionNumber": factory.LazyAttribute(lambda _: faker.md5(raw_output=False)),
            "StudyInstanceUID": factory.LazyFunction(uid),
            "Manufacturer": factory.Iterator(["HOLOGIC, INC.", "GE", "SIEMENS"]),
            "ManufacturerModelName": factory.Iterator(["Lorad"]),
            "Modality": factory.Iterator(["MG", "XR", "CT"]),
            "StudyDate": factory.LazyAttribute(
                lambda _: faker.date_between(
                    datetime.strptime("2010-01-01", "%Y-%m-%d"),
                    datetime.strptime("2022-01-01", "%Y-%m-%d"),
                ).strftime("%Y%m%d")
            ),
            "ReferringPhysicianName": factory.LazyAttribute(lambda _: faker.name()),
            "StudyDescription": factory.Iterator(
                ["XRAY IMAGING", "PET SCAN LEFT SIDE", "SPINAL IMAGING LOWER"]
            ),
            "StudyTime": factory.LazyAttribute(
                lambda _: faker.time_object().strftime("%H%M%S") + ".000000"
            ),
        }
    )

    image_attrs: dict = None

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        model = model_class()
        attrs = {**kwargs.get("default_image_attrs"), **(kwargs.get("image_attrs") or {})}
        model.image_paths = kwargs["image_paths"]
        model.num_images = kwargs["num_images"]
        model.images = [
            ImageFactory(
                image_path=model.image_paths[i % len(model.image_paths)],
                **attrs,
            )
            for i in range(model.num_images)
        ]
        return model


for i, img in enumerate(
    ExamFactory(
        num_images=0,
        image_dir="/Users/dcardoza/Dropbox/Media/Pictures/cyberpunk",
        image_attrs={
            "Modality": "MG",
            "StudyDescription": "BREAST IMAGING TOMOSYNTHESIS",
            "Manufacturer": "HOLOGIC, INC.",
            "ManufacturerModelName": "LORAD",
        },
    ).images
):
    img: pydicom.Dataset
    #    print(img)
    img.save_as(f"output/image_{i}.dcm", write_like_original=False)


for img in ImageFactory.build_batch(12, PatientID="123456", Modality="MG", StudyDescription="LOL"):
    print(img)
