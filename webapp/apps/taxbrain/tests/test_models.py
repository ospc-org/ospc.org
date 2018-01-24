from django.test import TestCase
from django.test import Client
import json
import os
import pytest
import numpy as np
from datetime import datetime

from ..models import JSONReformTaxCalculator
from ...test_assets.utils import get_taxbrain_model

START_YEAR = 2016

CURDIR = os.path.abspath(os.path.dirname(__file__))

class TaxBrainJSONReformModelTest(TestCase):
    """Test taxbrain JSONReformTaxCalculator."""

    def setUp(self):
        # Every test needs a client.
        self.test_string = "".join(["1" for x in range(100000)])

    def test_create_reforms(self):
        self.reforms = JSONReformTaxCalculator.objects.create(
            reform_text=self.test_string,
            raw_reform_text=self.test_string,
            assumption_text=self.test_string,
            raw_assumption_text=self.test_string
        )

@pytest.mark.usefixtures("test_coverage_fields")
class TaxBrainResultsTest(TestCase):

    def setUp(self):
        pass


    def test_tc_lt_0130(self):
        old_path = os.path.join(CURDIR, "skelaton_res_lt_0130.json")
        with open(old_path) as js:
            old_labels = json.loads(js.read())

        new_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(new_path) as js:
            new_labels = json.loads(js.read())

        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.10.2",
                                        webapp_vers="1.1.1")

        model = unique_url.unique_inputs
        model.tax_result = old_labels
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.tax_result, new_labels)


    def test_tc_gt_0130(self):
        old_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(old_path) as js:
            old_labels = json.loads(js.read())

        new_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(new_path) as js:
            new_labels = json.loads(js.read())

        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.13.0",
                                        webapp_vers="1.2.0")

        model = unique_url.unique_inputs
        model.tax_result = old_labels
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.tax_result, new_labels)
