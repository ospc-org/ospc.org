from django.test import TestCase
from django.test import Client
import json
import os
import pytest
import numpy as np
from datetime import datetime

from ..taxbrain.models import (JSONReformTaxCalculator,
                               OutputUrl)
from utils import get_taxbrain_model, stringify_fields
from ..taxbrain.forms import TaxBrainForm

START_YEAR = 2016

CURDIR = os.path.abspath(os.path.dirname(__file__))

@pytest.mark.usefixtures("test_coverage_fields", "test_coverage_gui_fields",
                         "test_coverage_behavioral_fields")
class TaxBrainModelsTest:

    def setUp(self):
        pass


@pytest.mark.usefixtures("skelaton_res_lt_0130",
                         "skelaton_res_gt_0130")
class TaxBrainTableResults(TaxBrainModelsTest):

    def tc_lt_0130(self, fields, Form=TaxBrainForm, UrlModel=OutputUrl):
        unique_url = get_taxbrain_model(fields,
                                        taxcalc_vers="0.10.2.abc",
                                        webapp_vers="1.1.1",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = self.skelaton_res_lt_0130
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(),
                                self.skelaton_res_gt_0130)

    def tc_gt_0130(self, fields, Form=TaxBrainForm, UrlModel=OutputUrl):
        unique_url = get_taxbrain_model(fields,
                                        taxcalc_vers="0.13.0",
                                        webapp_vers="1.2.0",
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = self.skelaton_res_gt_0130
        model.creation_date = datetime.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(),
                                self.skelaton_res_gt_0130)


class TaxBrainFieldsTest(TaxBrainModelsTest):

    def parse_fields(self, start_year, fields, Form=TaxBrainForm,
                     exp_result=None):
        start_year = 2017
        fields = stringify_fields(fields)
        form = Form(start_year, fields)

        # returns model object but does not save to the database
        model = form.save(commit=False)

        # parse fields--map to package name and cast input strings to python
        # vals as specified by upstream package
        model.set_fields()
        model.save()
        # get formatted model specifications
        results = model.get_model_specs()
        # do some kind of check here using `exp_result`
