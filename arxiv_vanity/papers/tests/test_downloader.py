import unittest
from ..downloader import arxiv_id_to_source_url, guess_extension_from_headers


class DownloaderTest(unittest.TestCase):
    def test_arxiv_id_to_source_url(self):
        self.assertEqual(arxiv_id_to_source_url('1708.03313'), 'https://arxiv.org/e-print/1708.03313')

    def test_guess_extension_from_headers(self):
        self.assertEqual(guess_extension_from_headers({
            'content-type': 'application/pdf',
        }), '.pdf')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/postscript',
        }), '.ps.gz')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-eprint-tar',
        }), '.tar.gz')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-eprint',
        }), '.tex.gz')
        self.assertEqual(guess_extension_from_headers({
            'content-encoding': 'x-gzip',
            'content-type': 'application/x-dvi',
        }), '.dvi.gz')
