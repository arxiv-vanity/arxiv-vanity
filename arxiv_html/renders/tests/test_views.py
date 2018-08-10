from unittest.mock import patch
from rest_framework.test import APITestCase
from ..models import Render


class ViewsTest(APITestCase):
    def test_put_creates_a_new_render(self):
        with patch.object(Render, 'delay') as mock_delay:
            response = self.client.put("/renders?id_type=arxiv&paper_id=1234.5678v2")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data["id_type"], "arxiv")
            self.assertEqual(response.data["paper_id"], "1234.5678v2")
            self.assertEqual(response.data["state"], "PENDING")
            self.assertEqual(response.data["html_url"], None)

        mock_delay.assert_called_once_with()

        with patch.object(Render, 'delay') as mock_delay:
            response = self.client.put("/renders?id_type=arxiv&paper_id=1234.5678v2")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["id_type"], "arxiv")
            self.assertEqual(response.data["paper_id"], "1234.5678v2")
            self.assertEqual(response.data["state"], "PENDING")
            self.assertEqual(response.data["html_url"], None)

        mock_delay.assert_not_called()
