import dicom_fixtures


def test_basic():
    pid, acc = "testpatient", "testaccession"
    img = dicom_fixtures.ImageFactory(PatientID=pid, AccessionNumber=acc)
    assert img.PatientID == pid
    assert img.AccessionNumber == acc


def test_save(tmp_path):
    ds = dicom_fixtures.ImageFactory()
    ds.save_as(tmp_path / "test.dcm")
