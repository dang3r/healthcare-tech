import concurrent.futures
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

import click


def has_text(fname: str) -> bool:
    """
    Check if a PDF file has text.
    A PDF file has text if it has fonts
    """
    result = subprocess.run(
        f"pdffonts {fname}", encoding="utf8", shell=True, stdout=subprocess.PIPE
    )
    if result.returncode != 0:
        return False
    return len(result.stdout.split("\n")) > 2


def process(src_fname: str, dst_fname: str) -> None:
    """
    Extract text from a given PDF file into a text file
    """
    if has_text(src_fname):
        ret = subprocess.run(f"pdftotext {src_fname} {dst_fname}", shell=True)
    else:
        ret = subprocess.run(
            f"ocrmypdf --sidecar {dst_fname} {src_fname} fake.pdf", shell=True
        )

    if ret.returncode != 0:
        print(f"Processing {src_fname} failed")
        return
    print(f"Processing {src_fname} succeeded")


@click.command()
@click.option("--src-dir", required=True)
@click.option("--dst-dir", default="text")
@click.option("--dry-run", default=True)
def main(src_dir: str, dst_dir: str, dry_run: bool):
    os.makedirs(dst_dir, exist_ok=True)
    src_file_names = os.listdir(src_dir)
    src_file_paths = [os.path.join(src_dir, fname) for fname in src_file_names]
    dst_file_paths = [os.path.join(dst_dir, fname[:-3] + "txt") for fname in src_file_names]
    print("{} PDF files found".format(len(src_file_names)))

    if dry_run:
        return

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process, src_fname, dst_fname)
            for src_fname, dst_fname in zip(src_file_paths, dst_file_paths)
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                pass

if __name__ == "__main__":
    main()