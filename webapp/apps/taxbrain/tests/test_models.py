from django.test import TestCase
import pytest

from ..models import JSONReformTaxCalculator
from ..forms import TaxBrainForm
from ...test_assets.utils import get_taxbrain_model
from ...test_assets.test_models import TaxBrainTableResults, TaxBrainModelsTest


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


class TaxBrainStaticResultsTest(TaxBrainTableResults, TestCase):

    def test_static_tc_lt_0130(self):
        self.tc_lt_0130()

    def test_static_tc_gt_0130(self):
        self.tc_gt_0130()


class TaxBrainFieldsTest(TaxBrainModelsTest, TestCase):

    def test_set_fields(self):
        fields = self.test_coverage_fields.copy()
        fields.pop('_state', None)
        fields.pop('creation_date', None)
        fields.pop('id', None)
        for key in fields:
            if isinstance(fields[key], list):
                fields[key] = ','.join(map(str, fields[key]))
        first_year = fields.get('first_year', 2017)
        form = TaxBrainForm(first_year, fields)

        model = form.save(commit=False)

        # model.set_fields(form)
        # model.save()
        results = model.get_model_specs()
        model.save()
        print(results)
