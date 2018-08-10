from rest_framework.test import APITestCase
import time
import timeout_decorator


class IntegrationTest(APITestCase):
    """
    Tests the entire rendering system using a local file.
    """
    @timeout_decorator.timeout(5)
    def test_creating_a_successful_render(self):
        response = self.client.put("/renders?id_type=arxiv&paper_id=1234.5678v2")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["id_type"], "arxiv")
        self.assertEqual(response.data["paper_id"], "1234.5678v2")
        self.assertEqual(response.data["state"], "PENDING")
        self.assertEqual(response.data["html_url"], None)

        while response.data["state"] in ("PENDING", "STARTED"):
            response = self.client.put("/renders?id_type=arxiv&paper_id=1234.5678v2")
            self.assertEqual(response.status_code, 200)
            time.sleep(0.1)

        self.assertEqual(response.data["state"], "SUCCESS")
