import click
from pydicom.filewriter import write_file_meta_info
from pynetdicom import AE, evt, AllStoragePresentationContexts, debug_logger

debug_logger()

@click.command()
@click.option("--pdu-size", "-p", type=int, default=16384)
@click.option("--maximum-associations", "-m", type=int, default=10)
def main(pdu_size: int, maximum_associations: int) -> None:
    def handle_store(event):
        """Handle a C-STORE request event."""
        try:
            print("Received a C_STORE requests")
            with open("server_data/" + event.request.AffectedSOPInstanceUID + ".dcm", 'wb') as f:
                f.write(b'\x00' * 128)
                f.write(b'DICM')
                write_file_meta_info(f, event.file_meta)
                f.write(event.request.DataSet.getvalue())
            return 0x0000
        except Exception as err:
            print(err)
    def handle_echo(event):
        return 0
    print("Maximum pdu size is", pdu_size)
    handlers = [(evt.EVT_C_STORE, handle_store), (evt.EVT_C_ECHO, handle_echo)]
    ae = AE("DC_SCP")
    ae.maximum_associations = maximum_associations
    ae.maximum_pdu_size  = pdu_size
    ae.supported_contexts = AllStoragePresentationContexts
    ae.start_server(('', 11112), evt_handlers=handlers)

if __name__ == "__main__":
    main()
