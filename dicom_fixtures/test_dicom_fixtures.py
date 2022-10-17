import time

import pytest
from pynetdicom import AE, AllStoragePresentationContexts, debug_logger, evt

import dicom_fixtures

debug_logger()


@pytest.fixture()
def dicom_scp():
    """A DICOM server supporting the C_STORE API"""

    def handle_store(event):
        """Handle a C-STORE request event."""
        return 0x0000

    # Start DICOM SCP
    handlers = [(evt.EVT_C_STORE, handle_store)]
    scp = AE()
    scp.supported_contexts = AllStoragePresentationContexts
    scp.start_server(("127.0.0.1", 11112), evt_handlers=handlers, block=False)
    yield

    scp.shutdown()


def test_basic():
    pid, acc = "testpatient", "testaccession"
    img = dicom_fixtures.ImageFactory(PatientID=pid, AccessionNumber=acc)
    assert img.PatientID == pid
    assert img.AccessionNumber == acc


def test_save(tmp_path):
    """Verify the generated image can be saved"""
    ds = dicom_fixtures.ImageFactory()
    ds.save_as(tmp_path / "test.dcm")


def test_exam():
    """Verify that the exam factory generates a good set of images"""
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

    assert len(imgs) == 8

    for img in imgs:
        for attr, val in image_attrs.items():
            assert getattr(img, attr) == val


def test_c_store(dicom_scp):
    """Verify that the generated DICOM can be sent to a DICOM server"""
    ds = dicom_fixtures.ImageFactory()

    ae = AE()
    ae.add_requested_context("1.2.840.10008.5.1.4.1.1.7")
    assoc = ae.associate("127.0.0.1", 11112)
    assert assoc.is_established
    status = assoc.send_c_store(ds)
    assert status
    assoc.release()
