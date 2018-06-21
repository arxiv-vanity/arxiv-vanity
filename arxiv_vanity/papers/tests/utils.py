import datetime
import os
import shutil
import uuid
from django.conf import settings
from ..models import Paper, Render, SourceFileBulkTarball, SourceFile


def create_paper(arxiv_id=None, arxiv_version=None, title=None, updated=None,
                 source_file=None, arxiv_url=None, pdf_url=None,
                 categories=None):
    return Paper.objects.create(**{
        'arxiv_id': arxiv_id or uuid.uuid4(),
        'arxiv_version': arxiv_version if arxiv_version is not None else 1,
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


def create_source_file_bulk_tarball(num_items=None):
    return SourceFileBulkTarball.objects.create(
        filename="abc.tar",
        content_md5sum="edd8c013a86b474a9a934ecf673f479e",
        first_item="1111.2222",
        last_item="3333.4444",
        md5sum="af3a3f12f56feacb3c188cf262802a97",
        num_items=num_items if num_items is not None else 5,
        seq_num=3,
        size=2345678,
        timestamp="2000-01-01",
        yymm="0001"
    )


def create_source_file(arxiv_id=None, file=None):
    return SourceFile.objects.create(
        arxiv_id=arxiv_id or uuid.uuid4(),
        file=file
    )
