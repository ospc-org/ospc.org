from django.test import TestCase

from .models import TaxSaveInputs
from .models import convert_to_floats
from .helpers import default_parameters
import taxcalc
import ogusa


class DynamicTests(TestCase):

    def test_default_parameters_basic(self):
        out = default_parameters(2015)
        assert out
