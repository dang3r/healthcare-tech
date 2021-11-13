import random
import sys
from time import perf_counter

import click
import pydicom
from pynetdicom import AE, build_context, debug_logger

#debug_logger()

def stderr(*args, **kwargs) -> None:
    print(*args, **kwargs, file=sys.stderr)

@click.command()
@click.option("--pdu-size", "-p", type=int, default=16384)
@click.argument("filename")
@click.argument("address")
@click.argument("port")
def main(pdu_size: int, filename: str, address: str, port: int) -> None:
    ae = AE()
    ae.maximum_pdu_size = pdu_size
    ae.dimse_timeout = 120
    ae.network_timeout = 120
    ae.acse_timeout = 120
    ds = pydicom.dcmread(filename)
    ds.SOPInstanceUID = ".".join(str(random.randint(1, 100)) for _ in range(5))
    contexts = [build_context(ds.SOPClassUID, [ds.file_meta.TransferSyntaxUID])]

    t1 = perf_counter()
    assoc = ae.associate(address, int(port), contexts=contexts)
    if assoc.is_established:
        status = assoc.send_c_store(ds)
        stderr(status)
        if status.Status == 0:
            t2 = perf_counter()
            print(t1, t2)
            stderr('C-STORE request status: 0x{0:04x}'.format(status.Status))
        else:
            stderr('Connection timed out, was aborted or received invalid response')
        assoc.release()
    else:
        stderr('Association rejected, aborted or never connected')

if __name__ == "__main__":
    main()