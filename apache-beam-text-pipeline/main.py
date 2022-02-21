import argparse
import io
import json
import logging
import pathlib
import re

import apache_beam as beam
import pdftotext
from apache_beam.io import fileio
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from google.cloud import storage


class ExtractText(beam.DoFn):
    def process(self, readable_file: fileio.ReadableFile):
        import io
        import pathlib
        import subprocess

        import pdftotext
        from google.cloud import storage

        full_path = pathlib.Path(readable_file.metadata.path)
        file_path = pathlib.Path(*full_path.parts[2:])
        name = full_path.name
        client = storage.Client()
        bucket = client.get_bucket("fda_devices")
        blob = bucket.get_blob(str(file_path))

        text = ""
        f = io.BytesIO(blob.download_as_bytes())
        pdf = pdftotext.PDF(f)
        text = "\n\n".join(pdf)

        if len(text) < 100:
            txt_filepath = name + ".txt"
            src_filepath = name
            with open(src_filepath, "wb") as g:
                g.write(f.getvalue())

            ret = subprocess.run(
                f"ocrmypdf --sidecar {txt_filepath} {src_filepath} /tmp/fake.pdf", shell=True
            )
            with open(txt_filepath, "r") as f:
                text = f.read()

        return [(name, text)]


class ExtractPredicates(beam.DoFn):
    def process(self, val):
        import json
        import re

        device, text = val
        ret = []
        for match in re.findall(r"((K|DEN|P|PMA)\d{5,})", text, flags=re.DOTALL):
            ret.append(match[0])
        print(device, ret)
        return [json.dumps({"device": device, "predicates": ret})]


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
        max_num_workers=1,
        num_workers=1,
        machine_type="n2-standard-16",
        service_account_email="dataflow@health-tech-340502.iam.gserviceaccount.com",
        worker_harness_container_image="gcr.io/health-tech-340502/predicate:0.1.0",
        sdk_container_image="gcr.io/health-tech-340502/predicate:0.1.0",
    )

    # The pipeline will be run on exiting the with block.
    with beam.Pipeline(options=pipeline_options) as pipeline:
        filenames = (
            pipeline
            | "Expand file patterns from GCS" >> fileio.MatchFiles(known_args.input_pattern)
            | "Extract files" >> fileio.ReadMatches()
            | "Reshuffle (rebalance across workers)" >> beam.Reshuffle()
            | "Extract text from PDFs" >> beam.ParDo(ExtractText())
            | "Extract predicates from text" >> beam.ParDo(ExtractPredicates())
            | "WriteToFile" >> beam.io.WriteToText(known_args.output_path, num_shards=1)
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
