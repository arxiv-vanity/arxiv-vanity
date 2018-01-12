import datetime
import os
from django.test import TestCase
from ..query import parse

TEST_DATA_PATH = os.path.join(os.path.dirname(__file__), 'test-data.xml')


class QueryTest(TestCase):
    maxDiff = None

    def test_parse(self):
        papers = parse(open(TEST_DATA_PATH).read())
        self.assertEqual(list(papers)[0], {
            'arxiv_id': '1708.03312',
            'arxiv_version': 1,
            'title': 'Radical-level Ideograph Encoder for RNN-based Sentiment Analysis of Chinese and Japanese',
            'published': datetime.datetime(2017, 8, 10, 17, 46, 28, tzinfo=datetime.timezone.utc),
            'updated': datetime.datetime(2017, 8, 10, 17, 46, 28, tzinfo=datetime.timezone.utc),
            'arxiv_url': 'http://arxiv.org/abs/1708.03312',
            'authors': [{'affiliation': [], 'name': 'Yuanzhi Ke'},
                        {'affiliation': [], 'name': 'Masafumi Hagiwara'}],
            'categories': ['cs.CL'],
            'comment': '12 pages, 4 figures',
            'doi': None,
            'journal_ref': None,
            'pdf_url': 'http://arxiv.org/pdf/1708.03312',
            'primary_category': 'cs.CL',
            'summary': '  The character vocabulary can be very large in non-alphabetic languages such\n'
                'as Chinese and Japanese, which makes neural network models huge to process such\n'
                'languages. We explored a model for sentiment classification that takes the\n'
                'embeddings of the radicals of the Chinese characters, i.e, hanzi of Chinese and\n'
                'kanji of Japanese. Our model is composed of a CNN word feature encoder and a\n'
                'bi-directional RNN document feature encoder. The results achieved are on par\n'
                'with the character embedding-based models, and close to the state-of-the-art\n'
                'word embedding-based models, with 90% smaller vocabulary, and at least 13% and\n'
                '80% fewer parameters than the character embedding-based models and word\n'
                'embedding-based models respectively. The results suggest that the radical\n'
                'embedding-based approach is cost-effective for machine learning on Chinese and\n'
                'Japanese.\n',
        })
