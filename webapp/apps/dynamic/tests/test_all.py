from django.test import TestCase

from ...taxbrain.helpers import default_policy
import taxcalc

class DynamicTests(TestCase):

    def test_default_policy_basic(self):
        out = default_policy(2015)
        assert out
