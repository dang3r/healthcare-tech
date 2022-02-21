FROM apache/beam_python3.7_sdk:2.36.0

RUN apt update
RUN apt install -y build-essential
RUN apt install -y libpoppler-cpp-dev
RUN apt install -y pkg-config
RUN apt install -y ocrmypdf

RUN pip3 install pdftotext google-cloud-storage==2.1.0

COPY main.py /main.py

ENTRYPOINT [ "/opt/apache/beam/boot" ]
