import dicom_fixtures


def test_basic():
    pid, acc = "testpatient", "testaccession"
    img = dicom_fixtures.ImageFactory(PatientID=pid, AccessionNumber=acc)
    assert img.PatientID == pid
    assert img.AccessionNumber == acc


def test_save(tmp_path):
    ds = dicom_fixtures.ImageFactory()
    ds.save_as(tmp_path / "test.dcm")


def test_exam():
    image_attrs = {
        "Modality": "MG",
        "StudyDescription": "BREAST IMAGING TOMOSYNTHESIS",
        "Manufacturer": "HOLOGIC, INC.",
        "ManufacturerModelName": "LORAD",
    }
    imgs = dicom_fixtures.ExamFactory(
        num_images=8,
        image_attrs=image_attrs,
    ).images

    for img in imgs:
        for attr, val in image_attrs.items():
            assert getattr(img, attr) == val
