import datetime
import os
import shutil
import uuid
from django.conf import settings
from ..models import Paper, Render


def create_paper(arxiv_id=None, title=None, updated=None, source_file=None,
                 arxiv_url=None, pdf_url=None, categories=None):
    return Paper.objects.create(**{
        'arxiv_id': arxiv_id or uuid.uuid4(),
        'title': title or 'Radical-level Ideograph Encoder for RNN-based Sentiment Analysis of Chinese and Japanese',
        'published': datetime.datetime(2017, 8, 10, 17, 46, 28, tzinfo=datetime.timezone.utc),
        'updated': updated or datetime.datetime(2017, 8, 10, 17, 46, 28, tzinfo=datetime.timezone.utc),
        'arxiv_url': arxiv_url or 'http://arxiv.org/abs/1708.03312v1',
        'authors': [{'affiliation': [], 'name': 'Yuanzhi Ke'},
                    {'affiliation': [], 'name': 'Masafumi Hagiwara'}],
        'categories': categories or ['cs.CL'],
        'comment': '12 pages, 4 figures',
        'doi': None,
        'journal_ref': None,
        'pdf_url': pdf_url or 'http://arxiv.org/pdf/1708.03312v1',
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
        'source_file': source_file,
    })


def create_render(paper=None, state=None):
    return Render.objects.create(
        paper=paper or create_paper(),
        state=state or Render.STATE_UNSTARTED
    )


def create_render_with_html(paper=None):
    render = create_render(paper=paper, state=Render.STATE_SUCCESS)
    source_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'render.html')
    output_dir = os.path.join(settings.MEDIA_ROOT, 'render-output', str(render.id))
    os.makedirs(output_dir)
    shutil.copyfile(source_path, os.path.join(output_dir, 'index.html'))
    return render
