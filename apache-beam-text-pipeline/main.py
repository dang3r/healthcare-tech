import argparse
import logging

import apache_beam as beam
from apache_beam.io import ReadFromText, WriteToText, fileio
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions


def run(argv=None) -> None:
    """Main entry point; defines and runs the wordcount pipeline."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-pattern",
        default="gs://fda_devices/raw/**.pdf",
        help="Glob pattern of input pdfs to process",
    )
    known_args, pipeline_args = parser.parse_known_args(argv)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(pipeline_args)
    #    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    # The pipeline will be run on exiting the with block.
    with beam.Pipeline(options=pipeline_options) as pipeline:

        # Read the text file[pattern] into a PCollection.
        #        lines = p | "Read" >> ReadFromText(known_args.input)
        filenames = (
            pipeline
            | "Expand file patterns from GCS" >> fileio.MatchFiles(known_args.input_pattern)
            | "Extract files" >> fileio.ReadMatches()
            | "Print" >> beam.Map(lambda x: print(x))
            #            | "Reshuffle (rebalance across workers)" >> beam.Reshuffle()
        )

    """
        counts = (
            lines
            | "Split" >> (beam.ParDo(WordExtractingDoFn()).with_output_types(str))
            | "PairWithOne" >> beam.Map(lambda x: (x, 1))
            | "GroupAndSum" >> beam.CombinePerKey(sum)
        )

        # Format the counts into a PCollection of strings.
        def format_result(word, count):
            return "%s: %d" % (word, count)

        output = counts | "Format" >> beam.MapTuple(format_result)

        # Write the output using a "Write" transform that has side effects.
        # pylint: disable=expression-not-assigned
        output | "Write" >> WriteToText(known_args.output)
    """


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
