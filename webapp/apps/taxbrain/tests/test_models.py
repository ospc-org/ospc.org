from django.test import TestCase
from django.test import Client
import json
import os
from datetime import datetime

from ..models import TaxSaveInputs, JSONReformTaxCalculator, OutputUrl
from ..forms import PersonalExemptionForm
from ...test_assets.test_reform import test_coverage_fields as fields

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

class TaxBrainResultsTest(TestCase):

    def setUp(self):
        pass

    def get_taxbrain_model(self):
        del fields['_state']
        del fields['creation_date']
        del fields['id']
        for key in fields:
            if isinstance(fields[key], list):
                fields[key] = ','.join(map(str, fields[key]))
        personal_inputs = PersonalExemptionForm(2017, fields)
        print(personal_inputs.errors)
        model = personal_inputs.save()
        model.job_ids = '1,2,3'
        model.json_text = None
        model.first_year = 2017
        model.quick_calc = False
        model.save()

        unique_url = OutputUrl()
        unique_url.taxcalc_version = "0.10.2"
        unique_url.webapp_vers = "1.1.0"
        unique_url.unique_inputs = model
        unique_url.model_pk = model.pk
        unique_url.exp_comp_datetime = "2017-10-10"
        unique_url.save()

        return unique_url

    def test_tc_lt_0130(self):
        old_path = os.path.join(CURDIR, "skelaton_tc_lt_0130.json")
        with open(old_path) as js:
            old_labels = js.read()

        new_path = os.path.join(CURDIR, "skelaton_tc_gt_0130.json")
        with open(new_path) as js:
            new_labels = js.read()

        unique_url = self.get_taxbrain_model()

        model = unique_url.unique_inputs
        model.tax_result = old_labels
        model.creation_date = datetime.now()

        assert model.tax_result == new_labels
