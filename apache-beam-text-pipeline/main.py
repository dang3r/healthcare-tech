import argparse
import contextlib
import io
import json
import logging
import os
import pathlib
import re
import traceback
from datetime import datetime
from typing import List, Tuple

import apache_beam as beam
import pdftotext
from apache_beam.io import fileio
from apache_beam.metrics import Metrics
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from google.cloud import storage

NOW = datetime.now().strftime("%Y-%m-%d-%H:%M")


class ExtractText(beam.DoFn):
    def __init__(self):
        self.errors = Metrics.counter(self.__class__, "errors")
        self.successes = Metrics.counter(self.__class__, "successes")

    def process(self, readable_file: fileio.ReadableFile) -> List[Tuple[str, str]]:
        import contextlib
        import io
        import pathlib
        import subprocess

        import pdftotext
        from google.cloud import storage

        try:
            full_path = pathlib.Path(readable_file.metadata.path)
            file_path = pathlib.Path(*full_path.parts[2:])
            name = full_path.name

            logging.info(f"Processing pdf file {full_path}. name={name}")
            client = storage.Client()
            bucket = client.get_bucket("fda_devices")
            blob = bucket.get_blob(str(file_path))
            text = ""
            f = io.BytesIO(blob.download_as_bytes())
            pdf = pdftotext.PDF(f)
            text = "\n\n".join(pdf)

            if len(text) < 100:
                logging.info(f"No text found in {full_path}. Extracting text using OCR")
                txt_filepath = name + ".txt"
                src_filepath = name
                with open(src_filepath, "wb") as g:
                    g.write(f.getvalue())

                ret = subprocess.run(
                    f"ocrmypdf --sidecar {txt_filepath} {src_filepath} /tmp/{name}.pdf", shell=True
                )
                ret.check_returncode()
                with open(txt_filepath, "r") as f:
                    text = f.read()
                with contextlib.suppress(FileNotFoundError):
                    os.remove(txt_filepath)
                with contextlib.suppress(FileNotFoundError):
                    os.remove(src_filepath)

            # Remove `.pdf` from the filename
            knumber = name[:-4]
            self.successes.inc()
            return [(knumber, text)]
        except Exception as err:
            logging.error(err)
            self.errors.inc()
            logging.error(f"Error processing {full_path}")
            logging.error(traceback.format_exc())


class ExtractPredicates(beam.DoFn):
    def __init__(self):
        self.errors = Metrics.counter(self.__class__, "errors")
        self.successes = Metrics.counter(self.__class__, "successes")

    def process(self, val: Tuple[str, str]):
        import json
        import re

        device, text = val
        ret = []
        for match in re.findall(r"((K|DEN|P|PMA)\d{5,})", text, flags=re.DOTALL):
            ret.append(match[0])
        print(device, ret)
        self.successes.inc()
        return [json.dumps({"device": device, "predicates": ret})]


class WriteTextToStorage(beam.DoFn):
    def __init__(self, path_prefix=f"dataflow/{NOW}"):
        self.path_prefix = path_prefix
        self.errors = Metrics.counter(self.__class__, "errors")
        self.successes = Metrics.counter(self.__class__, "successes")

    def process(self, stuff: Tuple[str, str]) -> None:
        from google.cloud import storage

        name, text = stuff
        client = storage.Client()
        bucket = client.get_bucket("fda_devices")
        blob = bucket.blob(f"{self.path_prefix}/{name}")
        blob.upload_from_string(text)
        self.successes.inc()


def run(argv=None) -> None:
    """Main entry point; defines and runs the wordcount pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-pattern",
        default="gs://fda_devices/raw/**.pdf",
        help="Glob pattern of input pdfs to process",
    )
    parser.add_argument(
        "--output-path",
        default="gs://fda_devices/output/graph.jsonl",
        help="Filepath to where the jsonl graph file lives",
    )
    known_args, pipeline_args = parser.parse_known_args(argv)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(
        pipeline_args,
        runner="DataflowRunner",
        project="health-tech-340502",
        region="us-central1",
        experiments=["use_runner_v2"],
        max_num_workers=8,
        num_workers=8,
        machine_type="n2-standard-16",
        number_of_worker_harness_threads=4,
        service_account_email="dataflow@health-tech-340502.iam.gserviceaccount.com",
        worker_harness_container_image="gcr.io/health-tech-340502/predicate:0.1.0",
        sdk_container_image="gcr.io/health-tech-340502/predicate:0.1.0",
    )

    # The pipeline will be run on exiting the with block.
    # fmt: off
    with beam.Pipeline(options=pipeline_options) as pipeline:
        device_text = (
            pipeline
            | "Expand file patterns from GCS" >> fileio.MatchFiles(known_args.input_pattern)
            | "Extract files" >> fileio.ReadMatches()
            | "Reshuffle (rebalance across workers)" >> beam.Reshuffle()
            | "Extract text from PDFs" >> beam.ParDo(ExtractText())
        )

        _ = (
            device_text
            | "Extract predicates from text" >> beam.ParDo(ExtractPredicates())
            | "WriteToFile" >> beam.io.WriteToText(f"gs://fda_devices/dataflow/{NOW}/graph.jsonl", num_shards=1)
        )
        _ = (
            device_text
            | "Push Text to GCS" >> beam.ParDo(WriteTextToStorage())
        )
    # fmt: on


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
