from django.test import TestCase
from django.test import Client
import json
import os
import pytest
import numpy as np
from datetime import datetime

from ..taxbrain.models import (JSONReformTaxCalculator,
                               OutputUrl)
from utils import get_taxbrain_model
from ..taxbrain.forms import TaxBrainForm

START_YEAR = 2016

CURDIR = os.path.abspath(os.path.dirname(__file__))

@pytest.mark.usefixtures("test_coverage_fields")
class TaxBrainModelsTest:

    def setUp(self):
        pass


@pytest.mark.usefixtures("skelaton_res_lt_0130",
                         "skelaton_res_gt_0130")
class TaxBrainTableResults(TaxBrainModelsTest):

    def tc_lt_0130(self, Form=TaxBrainForm, UrlModel=OutputUrl):
        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.10.2.abc",
                                        webapp_vers="1.1.1",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = self.skelaton_res_lt_0130
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(),
                                self.skelaton_res_gt_0130)

    def tc_gt_0130(self, Form=TaxBrainForm, UrlModel=OutputUrl):
        unique_url = get_taxbrain_model(self.test_coverage_fields,
                                        taxcalc_vers="0.13.0",
                                        webapp_vers="1.2.0",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = self.skelaton_res_gt_0130
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(),
                                self.skelaton_res_gt_0130)
