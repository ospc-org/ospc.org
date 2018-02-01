from django.test import TestCase
from django.test import Client
import json
import os
import pytest
import numpy as np
from datetime import datetime

from ..models import (JSONReformTaxCalculator,
                      OutputUrl)
from ...test_assets.utils import get_taxbrain_model
from ..forms import PersonalExemptionForm

from ...dynamic.models import DynamicBehaviorOutputUrl
from ...dynamic.forms import DynamicBehavioralInputsModelForm

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

    def tc_lt_0130(self, Form=PersonalExemptionForm, UrlModel=OutputUrl):
        old_path = os.path.join(CURDIR, "skelaton_res_lt_0130.json")
        with open(old_path) as js:
            old_labels = json.loads(js.read())

        new_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(new_path) as js:
            new_labels = json.loads(js.read())

        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.10.2.abc",
                                        webapp_vers="1.1.1",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = old_labels
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(), new_labels)

    def tc_gt_0130(self, Form=PersonalExemptionForm, UrlModel=OutputUrl):
        old_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(old_path) as js:
            old_labels = json.loads(js.read())

        new_path = os.path.join(CURDIR, "skelaton_res_gt_0130.json")
        with open(new_path) as js:
            new_labels = json.loads(js.read())

        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.13.0",
                                        webapp_vers="1.2.0",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = old_labels
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(), new_labels)


    def test_static_tc_lt_0130(self):
        self.tc_lt_0130()

    def test_static_tc_gt_0130(self):
        self.tc_gt_0130()


    def test_dynamic_tc_lt_0130(self):
        self.tc_lt_0130(Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)

    def test_dynamic_tc_gt_0130(self):
        self.tc_gt_0130(Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)
