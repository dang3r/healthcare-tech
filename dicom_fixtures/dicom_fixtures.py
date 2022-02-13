import string
from dataclasses import dataclass
from random import randint
from typing import List

import factory
import numpy as np
import pydicom
from PIL import Image
from pydicom.dataset import FileMetaDataset


def uid() -> str:
    return f"1.2.3.{randint(100000,99999999)}"


class ImageFactory(factory.Factory):
    class Meta:
        model = pydicom.Dataset

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
    StudyTime = "123213"
    Laterality = "R"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        d = model_class()
        for k, v in kwargs.items():
            setattr(d, k, v)
        #            d[k] = v
        return d

    @factory.post_generation
    def route_slot_stop_infos(self, create, extracted, **kwargs):
        print("DAN")
        im_frame = Image.open(
            "/Users/dcardoza/Dropbox/Media/Pictures/wallpaper//cyberpunk_2077___4k_wallpaper_2018___game_info__by_nurboyxvi-dcdx4ew.png"
        )  # the PNG file to be replace
        print("mode", im_frame.mode)
        if im_frame.mode == "L":
            # (8-bit pixels, black and white)
            np_frame = np.array(im_frame.getdata(), dtype=np.uint8)
            self.Rows = im_frame.height
            self.Columns = im_frame.width
            self.PhotometricInterpretation = "MONOCHROME1"
            self.SamplesPerPixel = 1
            self.BitsStored = 8
            self.BitsAllocated = 8
            self.HighBit = 7
            self.PixelRepresentation = 0
            self.PixelData = np_frame.tobytes()
        elif im_frame.mode == "RGBA":
            # RGBA (4x8-bit pixels, true colour with transparency mask)
            np_frame = np.array(im_frame.getdata(), dtype=np.uint8)[:, :3]
            self.Rows = im_frame.height
            self.Columns = im_frame.width
            self.PhotometricInterpretation = "RGB"
            self.SamplesPerPixel = 3
            self.BitsStored = 8
            self.BitsAllocated = 8
            self.HighBit = 7
            self.PixelRepresentation = 0
            self.PlanarConfiguration = 0
            self.PixelData = np_frame.tobytes()
        print("BRAG")
        self.file_meta = pydicom.Dataset()
        self.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
        self.file_meta.TransferSyntaxUID = "1.2.840.10008.1.2.1"
        return None


@dataclass
class Exam:
    num_images: int = 0
    images: list = None
    PatientID: str = ""
    PatientName: str = ""
    AccessionNumber: str = "123"
    StudyInstanceUID: str = ""
    Manufacturer: str = ""
    ManufacturerModelName: str = ""
    StudyDate: str = ""
    Modality: str = ""
    ReferringPhysicianName: str = ""
    StudyDescription: str = ""


class ExamFactory(factory.Factory):
    class Meta:
        model = Exam

    num_images = 4
    PatientID = factory.LazyFunction(
        lambda: "".join(string.ascii_lowercase[randint(0, 25)] for _ in range(10))
    )
    PatientName = factory.Faker("name")
    AccessionNumber = "123"
    StudyInstanceUID = factory.LazyFunction(uid)
    Manufacturer = factory.Iterator(["HOLOGIC, INC.", "GE", "SIEMENS"])
    ManufacturerModelName = factory.Iterator(["Lorad"])
    Modality = factory.Iterator(["MG", "XR", "CT"])
    StudyDate = "20210101"
    ReferringPhysicianName = factory.Faker("name")
    StudyDescription = factory.Iterator(
        ["XRAY IMAGING", "PET SCAN LEFT SIDE", "SPINAL IMAGING LOWER"]
    )

    images = factory.LazyAttribute(
        lambda o: [
            ImageFactory(
                PatientID=o.PatientID,
                PatientName=o.PatientName,
                AccessionNumber=o.AccessionNumber,
                StudyInstanceUID=o.StudyInstanceUID,
                Manufacturer=o.Manufacturer,
                StudyDate=o.StudyDate,
                StudyDescription=o.StudyDescription,
                ReferringPhysicianName=o.ReferringPhysicianName,
                Modality=o.Modality,
            )
            for _ in range(o.num_images)
        ]
    )


class MammographyExamFactory(ExamFactory):
    num_images = 4
    Manufacturer = factory.Iterator(["HOLOGIC, INC.", "GE", "SIEMENS"])
    ManufacturerModelName = factory.Iterator(["Lorad"])
    Modality = "MG"
    StudyDescription = "BREAST IMAGING TOMOSYNTHESIS"


dicom = ImageFactory()
print(dicom)


for i, img in enumerate(ExamFactory(num_images=1).images):
    print("Image", i)
    print(type(img))
    print(">> ", img)
    img.is_little_endian = True
    img.is_implicit_VR = False
    img.save_as("lol.dcm", write_like_original=False)
    input()

#
# for i, img in enumerate(ExamFactory(num_images=1).images):
#    print("Image", i)
#    print(">> ", img)
#
# for i, img in enumerate(MammographyExamFactory(num_images=1).images):
#    print("Image", i)
#    print(type(img))
#    print(">> ", img)
#
