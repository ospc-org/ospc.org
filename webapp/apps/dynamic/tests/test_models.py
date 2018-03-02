from django.test import TestCase
import pytest

from ...test_assets.utils import get_taxbrain_model
from ...test_assets.test_models import (TaxBrainTableResults,
                                        TaxBrainFieldsTest)

from ...dynamic.models import DynamicBehaviorOutputUrl
from ...dynamic.forms import DynamicBehavioralInputsModelForm


class TaxBrainDynamicResultsTest(TaxBrainTableResults, TestCase):

    def test_dynamic_tc_lt_0130(self):
        self.tc_lt_0130(self.test_coverage_behavioral_fields,
                        Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)

    def test_dynamic_tc_gt_0130(self):
        self.tc_gt_0130(self.test_coverage_behavioral_fields,
                        Form=DynamicBehavioralInputsModelForm,
                        UrlModel=DynamicBehaviorOutputUrl)


class TaxBrainDynamicFieldsTest(TaxBrainFieldsTest, TestCase):

    def test_set_fields(self):
        start_year = 2017
        fields = self.test_coverage_behavioral_gui_fields.copy()
        fields["first_year"] = start_year
        self.parse_fields(start_year, fields,
                          Form=DynamicBehavioralInputsModelForm)
