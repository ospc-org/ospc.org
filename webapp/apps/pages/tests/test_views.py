from django.test import TestCase


class PageViewsTests(TestCase):
    def test_redirects(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)

        extensions = [
            "portfolio",
            "team",
            "newsletter",
            "newsletter01092019",
            "newsletter12192018",
            "newsletter12052018",
            "newsletter11152018",
            "newsletter11022018",
            "signup",
            "subscribed",
            "donate",
        ]

        for ext in extensions:
            resp = self.client.get(f"/{ext}/")
            self.assertEqual(resp.status_code, 302)
