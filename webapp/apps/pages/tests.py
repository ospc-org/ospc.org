from django.test import TestCase


class PagesViewsTestCase(TestCase):
    def test_about(self):
        resp = self.client.get('/about/')
        self.assertEqual(resp.status_code, 200)

    def test_home(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_news(self):
        resp = self.client.get('/news/')
        self.assertEqual(resp.status_code, 302)

    def test_apps(self):
        resp = self.client.get('/apps/')
        self.assertEqual(resp.status_code, 200)
