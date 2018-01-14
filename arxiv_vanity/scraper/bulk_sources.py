import tarfile
import tempfile
import os

from django.core.files import File
from storages.backends.s3boto3 import S3Boto3Storage
from xml.etree import ElementTree

from ..papers.models import SourceFile, SourceFileBulkTarball


def update_bulk_sources():
    """
    Check for new bulk sources in the Arxiv bulk data S3 bucket:

    https://arxiv.org/help/bulk_data_s3

    If there are new sources, download them and put them into our S3 bucket.
    """
    print("Downloading manifest...")
    manifest = get_manifest()
    for f in manifest:
        # We've already processed this file, skip.
        # TODO: Re-process files which have been updated. (i.e. where md5 has
        # changed)
        try:
            tarball = SourceFileBulkTarball.objects.get(filename=f['filename'])
        except SourceFileBulkTarball.DoesNotExist:
            # This is a new file
            pass
        else:
            if tarball.has_correct_number_of_files():
                print(f"Skipping {f['filename']}")
                continue
            else:
                print(f"Reprocessing {f['filename']} because it has incorrect number of files")

        with tempfile.NamedTemporaryFile(suffix='tar') as tarfh:

            # Download new sources
            print(f"Downloading {f['filename']}...")
            download_tarball(f['filename'], tarfh.name)
            tarfh.flush()

            # Mark database as downloaded
            bulk_tarball = SourceFileBulkTarball.objects.get_or_create(
                filename=f['filename'],
                defaults=f
            )

            print(f"Extracting {f['filename']}...")
            for name, f in extract_tarball(tarfh.name):
                # Dedupe!
                # TODO: At some point, when we need to update papers, this should
                # instead update the file.
                if SourceFile.objects.filename_exists(name):
                    print(f"{name} already exists")
                    continue

                print(f"Saving {name}...")
                # Pass file handle directory to Django, which will stream the file
                # to S3 instead of loading into memory (in theory)
                wrapped_f = File(f)
                wrapped_f.name = name
                source_file = SourceFile.objects.create(
                    file=wrapped_f,
                    bulk_tarball=bulk_tarball
                )


def get_manifest():
    """
    Download and parse manifest from arxiv S3 bucket.
    """
    connection = S3Boto3Storage().connection
    obj = connection.Object('arxiv', 'src/arXiv_src_manifest.xml')
    s = obj.get(RequestPayer='requester')['Body'].read()
    return parse_manifest(s)


def parse_manifest(s):
    """
    Returns a list of files from a bulk source manifest XML string.
    """
    root = ElementTree.fromstring(s)
    result = []
    for f in root.findall("file"):
        # Turn it into a sensible dictionary
        d = {child.tag: child.text for child in f}
        # All the fields are text, apart from these which should be int
        for k in ('num_items', 'seq_num', 'size'):
            d[k] = int(d[k])
        result.append(d)
    return result


def download_tarball(key, local_filename):
    connection = S3Boto3Storage().connection
    bucket = connection.Bucket('arxiv')
    bucket.download_file(key, local_filename, {'RequestPayer': 'requester'})


def extract_tarball(path):
    """
    Returns an iterator of (filename, file object) tuples given a path to
    a tarball.
    """
    with tarfile.open(path, 'r:') as tar:
        for member in tar.getmembers():
            if member.isreg():
                yield os.path.basename(member.name), tar.extractfile(member.name)
