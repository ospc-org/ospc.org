from django.test import TestCase
import pytest

from ...test_assets.utils import get_taxbrain_model
from ...test_assets.test_models import TaxBrainTableResults

from ...dynamic.models import DynamicBehaviorOutputUrl
from ...dynamic.forms import DynamicBehavioralInputsModelForm


@pytest.mark.usefixtures("test_coverage_fields")
class TaxBrainDynamicResultsTest(TaxBrainTableResults, TestCase):

    def test_dynamic_tc_lt_0130(self):
        self.tc_lt_0130(Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)

    def test_dynamic_tc_gt_0130(self):
        self.tc_gt_0130(Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)
