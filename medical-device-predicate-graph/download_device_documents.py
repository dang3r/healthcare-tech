from google.cloud import storage
import click
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import concurrent
from datetime import datetime
import pandas as pd
 
def url(k_number: str, date: str) -> str:
    """Generate a URL for a FDA device given its K Number.

    Args:
        k_number: The fda device's K Number.
        date: The device's release date.

    Returns:
        A https URL containing the device's PDF summary.
    """
    year = int(date.split("/")[-1])
    if year <= 2001:
        return "https://www.accessdata.fda.gov/cdrh_docs/pdf/{}.pdf".format(k_number)
    return "https://www.accessdata.fda.gov/cdrh_docs/pdf{}/{}.pdf".format(year % 100, k_number)

def download_url(url: str) -> None:
    """Download a URL to a file

    Args:
        url: An http URL containing a PDF file
    """
    resp = requests.get(url)
    if resp.status_code != 200:
        print("Failed downloading url because of non-200 http status code: url='{}' status_code='{}'".format(url, resp.status_code))
        return
    elif resp.headers["content-type"] != "application/pdf":
        print("Failed downloading url because of non-pdf file : url='{}' content_type='{}'".format(url, resp.headers['content-type']))
        return

    fname = os.path.basename(url)
    dst = "raw/{}".format(fname)
    with open(dst, "wb") as f:
        f.write(resp.content)
    print("Downloaded url : url='{}'".format(url))

@click.command()
@click.option('--gcs-bucket', default="fda_devices")
@click.option('--gcp-project', default="health-tech-340502")
@click.option("--dst-folder", default="raw")
@click.option("--since", default="2021-01-01")
@click.option("--dry-run", default=True)
def main(gcs_bucket: str, gcp_project: str, dst_folder: str, since: str, dry_run: str):
    os.makedirs(dst_folder, exist_ok=True)

    # Get list of already downloaded documents
    client = storage.Client(project=gcp_project)
    downloaded_device_ids = set([blob.name[4:-4] for blob in client.list_blobs(gcs_bucket, prefix='raw')])
#    df = pd.read_csv("https://www.accessdata.fda.gov/premarket/ftparea/pmn96cur.zip", error_bad_lines=False, delimiter="|", encoding="latin")

    # Get list of new documents to download
    since_dt = datetime.strptime(since, "%Y-%m-%d")
    df = pd.read_csv("pmn96cur.zip", error_bad_lines=False, delimiter="|", encoding="latin")
    df["url"] = df.apply(lambda x: url(x["KNUMBER"], x["DATERECEIVED"]), axis=1)
    df['decision_date'] =  pd.to_datetime(df["DECISIONDATE"])
    df = df[(~df.KNUMBER.isin(downloaded_device_ids)) & (df.decision_date > since_dt)]
       

    print("{} documents already downloaded.".format(len(downloaded_device_ids)))
    print("Beginning download of {} pdfs".format(len(df)))

    if dry_run:
        return

    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_url = {executor.submit(download_url, url): url for url in df["url"]}
        for future in concurrent.futures.as_completed(future_to_url):
            _url = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (_url, exc))

if __name__ == "__main__":
    main()
