# Overview

This project experiments with tweaking the maximum size of a Protocol Data Unit (PDU) in the DICOM
network protocol and seeing its effects on sending DICOM data.

# Overview

The DICOM network protocol is used by medical imaging devices to communicate with one another. It provides an API for devices to:

- send or receive medical images (C_STORE)
- search a device for medical images or exams it is interested in (C_FIND)
- ping the device (C_ECHO)
- tell a device to push a set of images to another device (C_MOVE)

When performing any of these operations, the network data is split into chunks. These chunks have a maximum size set by
the maximum PDU length. When two devices establish a connection, this value is negotiated. It represents the maximum chunk size
a device will receive data. For example, if a Picture Archiving Communications Server (PACS) has a maximum pdu size of 1MB,
all images it receives (eg. from a mammography scanner) are split into 1MB chunks. For images that are large (Eg. 3D Tomosynthesis images),
this causes many chunks to be sent across the wire.

This project experiments with the maximum pdu length and its effect on receiving images.

# Hypothesis

When the maximum pdu length is much smaller than the image being transferred, this results in overhead that slows the image transfer.

# Code

### Prerequisites

- Python3
- Docker
- pynetdicom, click python libraries

### Run

```bash
$ ./run.sh 
Recreating dicom_pdu_size_server_1 ... done
Recreating dicom_pdu_size_server_1 ... done
Recreating dicom_pdu_size_server_1 ... done
Recreating dicom_pdu_size_server_1 ... done
Recreating dicom_pdu_size_server_1 ... done
Recreating dicom_pdu_size_server_1 ... done

# The total time it took to transfer images of certain sizes
./1MB_time.txt
78.945
./20MB_time.txt
82.034
./10MB_time.txt
79.775
./100KB_time.txt
86.160
./500KB_time.txt
81.273
./16KB_time.txt
136.263

$ python3 stats.py 
16KB   : mean=12.5s min=9.91s max=14.32s
100KB  : mean=7.41s min=4.26s max=8.68s
500KB  : mean=6.97s min=2.53s max=9.08s
1MB    : mean=6.65s min=03.4s max=7.92s
10MB   : mean=6.84s min=04.0s max=8.42s
20MB   : mean=7.08s min=4.09s max=8.57s
```

### How it works

A DICOM SCP is started with a different maximum pdu length. 4 DICOM SCUs / clients transfer a single 16MB image to the SCP in parallel. 100 images
are sent for each server configuration.

# Results

As expected, the smaller pdu lengths resulted in slower mean request times. The best mean request time was with a PDU of 1MB. For our file of 16MB, this means <=16 image data chunks
were sent to the DICOM SCP.

I was surprised that the 20MB pdu length was slower than 1MB or 10MB. Since 20MB > the length of the file, it should have sent the file in one big chunk.

```bash
$ python3 stats.py 
16KB   : mean=12.5s min=9.91s max=14.32s
100KB  : mean=7.41s min=4.26s max=8.68s
500KB  : mean=6.97s min=2.53s max=9.08s
1MB    : mean=6.65s min=03.4s max=7.92s
10MB   : mean=6.84s min=04.0s max=8.42s
20MB   : mean=7.08s min=4.09s max=8.57s
```

# Random Learnings

### Orthanc maximum pdu size

I usually use Orthanc as a local development PACS.  However, they limit the maximum pdu length to be in [4096,131072] / [2^12, 2^17]
so I did not use them.

### Dockerfile Entrypoint Syntax

When writing the Dockerfile for the dicom server, I used `ENTRYPOINT python3 -u /server.py` as the line for th entrypoint. I then passed
in the pdu length via the docker-compose file in the `command:` section. However, this failed to set the maximum pdu length successfully.

After a while, I found that the entrypoint has two forms: the `shell` and `exec` forms.

- exec  : `ENTRYPOINT ["python3",  "-u",  "/server.py"]`
- shell : `ENTRYPOINT python3 -u /server.py`

When using the `shell` form, you _cannot_ pass args or flags to the entrypoint process. With exec you can.

After switching to the exec format, everything worked :)

# Next Steps

- Test with other open-source DICOM SCPs / servers/ PACSes
- Test with images of different sizes.
- Determine why the 20MB file resulted in slower transfer times
- Clean up `run.sh` (eg. use less hardcoded pdu values)