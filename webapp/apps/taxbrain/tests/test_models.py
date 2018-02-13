from django.test import TestCase
import pytest

from ..models import JSONReformTaxCalculator
from ..forms import TaxBrainForm
from ...test_assets.utils import get_taxbrain_model, stringify_fields
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
        start_year = 2017
        fields = self.test_coverage_gui_fields.copy()
        fields = stringify_fields(fields)
        fields['first_year'] = start_year
        form = TaxBrainForm(start_year, fields)

        # returns TaxSaveInputs object but does not save to the database
        model = form.save(commit=False)

        # parse fields--map to package name and cast input strings to python
        # vals as specified by upstream package
        model.set_fields(form)
        model.save()
        # get formatted model specifications
        results = model.get_model_specs()
        # do some kind of check here
