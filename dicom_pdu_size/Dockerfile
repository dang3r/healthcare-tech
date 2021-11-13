FROM python:3.9.8-buster

RUN pip3 install pynetdicom click

COPY server.py /server.py

ENTRYPOINT ["python3",  "-u",  "/server.py"]