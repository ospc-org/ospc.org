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
from ...test_assets.test_models import TaxBrainTableResults
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
class TaxBrainResultsTest(TaxBrainTableResults, TestCase):

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
