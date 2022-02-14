import glob
import string
from dataclasses import dataclass
from datetime import datetime
from random import randint

import factory
import numpy as np
import pydicom
from faker import Faker
from PIL import Image

faker = Faker()


def uid() -> str:
    # TODO: How to create a great UID function to minimize collisions?
    return f"1.3.6.4.1.58139{randint(100000,99999999)}"


class ImageFactory(factory.Factory):
    class Meta:
        model = pydicom.Dataset
        strategy = factory.BUILD_STRATEGY
        # exclude = ("file",)

    _file = factory.Iterator(
        glob.glob("/Users/dcardoza/dev/healthcare-tech/dicom_fixtures/images/*")
    )

    PatientID = factory.LazyFunction(
        lambda: "".join(string.ascii_lowercase[randint(0, 25)] for _ in range(10))
    )
    PatientName = factory.Faker("name")
    AccessionNumber = "123"
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

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        d = model_class()
        for k, v in kwargs.items():
            if not k.startswith("_"):
                setattr(d, k, v)

        file = kwargs.get("_file")
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

    # Patient Information
    PatientID: str = ""
    PatientName: str = ""
    PatientBirthDate: str = ""

    # Exam Information
    AccessionNumber: str = "123"
    Modality: str = ""
    ReferringPhysicianName: str = ""
    StudyDescription: str = ""
    StudyDate: str = ""
    StudyTime: str = ""

    # Imaging Information
    Manufacturer: str = ""
    ManufacturerModelName: str = ""
    StudyInstanceUID: str = ""


class ExamFactory(factory.Factory):
    class Meta:
        model = Exam

    num_images = 4
    # img_paths: list = []

    PatientID = factory.LazyFunction(
        lambda: "".join(string.ascii_lowercase[randint(0, 25)] for _ in range(10))
    )
    PatientName = factory.Faker("name")
    PatientBirthDate = faker.date_of_birth(minimum_age=45, maximum_age=90).strftime("%Y%m%d")
    AccessionNumber = "123"
    StudyInstanceUID = factory.LazyFunction(uid)
    Manufacturer = factory.Iterator(["HOLOGIC, INC.", "GE", "SIEMENS"])
    ManufacturerModelName = factory.Iterator(["Lorad"])
    Modality = factory.Iterator(["MG", "XR", "CT"])
    #    StudyDate = "20210101"
    StudyDate = faker.date_between(
        datetime.strptime("2010-01-01", "%Y-%m-%d"),
        datetime.strptime("2022-01-01", "%Y-%m-%d"),
    ).strftime("%Y%m%d")
    ReferringPhysicianName = factory.Faker("name")
    StudyDescription = factory.Iterator(
        ["XRAY IMAGING", "PET SCAN LEFT SIDE", "SPINAL IMAGING LOWER"]
    )
    StudyTime = faker.time_object().strftime("%H%M%S") + ".000000"

    images = factory.LazyAttribute(
        lambda o: [
            ImageFactory(
                PatientID=o.PatientID,
                PatientName=o.PatientName,
                PatientBirthDate=o.PatientBirthDate,
                AccessionNumber=o.AccessionNumber,
                StudyInstanceUID=o.StudyInstanceUID,
                Manufacturer=o.Manufacturer,
                StudyDate=o.StudyDate,
                StudyDescription=o.StudyDescription,
                ReferringPhysicianName=o.ReferringPhysicianName,
                Modality=o.Modality,
                SeriesNumber=str(i),
                StudyTime=o.StudyTime,
            )
            for i in range(o.num_images)
        ]
    )


class MammographyExamFactory(ExamFactory):
    num_images = 4

    # Exam Fields
    Modality = "MG"
    StudyDescription = "BREAST IMAGING TOMOSYNTHESIS"

    # Imaging Fields
    Manufacturer = factory.Iterator(["HOLOGIC, INC.", "GE", "SIEMENS"])
    ManufacturerModelName = factory.Iterator(["Lorad"])


for i, img in enumerate(MammographyExamFactory(num_images=12).images):
    img: pydicom.Dataset
    img.save_as(f"image_{i}.dcm", write_like_original=False)
