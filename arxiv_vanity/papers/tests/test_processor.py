import unittest
from ..processor import process_render


class ProcessorTest(unittest.TestCase):
    def test_basics(self):
        html = """
<head>
<link href="style.css">
<style>body { }</style>
<script>blah</script>
</head>
<body>
<img src="fig.gif">
<img src="data:foo">
<a href="http://example.com">Hello</a>
<div class="ltx_abstract"><p>Science was done</p></div>
<figure class="ltx_figure"><img src="first_image.gif"></figure>
<script src="script.js" /></body>
"""
        output = process_render(html, "prefix", {})

        self.assertEqual(
            output["body"],
            """
<img src="prefix/fig.gif"/>
<img src="data:foo"/>
<a href="http://example.com" target="_blank">Hello</a>
<div class="ltx_abstract"><p>Science was done</p></div>
<figure class="ltx_figure"><img src="prefix/first_image.gif"/></figure>
<script src="prefix/script.js"></script>""",
        )
        self.assertEqual(output["links"], '<link href="prefix/style.css"/>\n')
        self.assertEqual(output["styles"], "<style>\n body { }\n</style>\n")
        self.assertEqual(output["scripts"], "<script>\n blah\n</script>\n")
        self.assertEqual(output["abstract"], "Science was done")
        self.assertEqual(output["first_image"], "prefix/first_image.gif")

    def test_arxiv_urls_are_converted_to_vanity_urls(self):
        html = '<head></head><a href="https://arxiv.org/abs/1710.06542">Something</a>'

        output = process_render(html, "", {})
        self.assertEqual(
            output["body"],
            '<a href="/papers/1710.06542/" target="_blank">Something</a>',
        )

    def test_emails_are_removed(self):
        html = '<head></head><a href="mailto:foo@bar.com">some email link</a> another@email.com'
        output = process_render(html, "", {})
        self.assertEqual(
            output["body"], "some email link ",
        )

