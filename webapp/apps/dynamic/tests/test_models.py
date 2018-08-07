from ...test_assets.test_models import (TaxBrainTableResults,
                                        TaxBrainFieldsTest)

from ...dynamic.models import DynamicBehaviorOutputUrl
from ...dynamic.forms import DynamicBehavioralInputsModelForm


class TestTaxBrainDynamicResults(TaxBrainTableResults):

    def test_dynamic_tc_lt_0130(self, test_coverage_behavioral_fields,
                                skelaton_res_lt_0130, skelaton_res_gt_0130):
        self.tc_table_backcompat(test_coverage_behavioral_fields,
                                 skelaton_res_lt_0130,
                                 skelaton_res_gt_0130,
                                 Form=DynamicBehavioralInputsModelForm,
                                 UrlModel=DynamicBehaviorOutputUrl,
                                 taxcalc_vers="0.10.2.abc",
                                 webapp_vers="1.1.1")

    def test_dynamic_tc_gt_0130(self, test_coverage_behavioral_fields,
                               skelaton_res_gt_0130):
        self.tc_table_backcompat(test_coverage_behavioral_fields,
                                 skelaton_res_gt_0130,
                                 skelaton_res_gt_0130,
                                 Form=DynamicBehavioralInputsModelForm,
                                 UrlModel=DynamicBehaviorOutputUrl,
                                 taxcalc_vers="0.13.0",
                                 webapp_vers="1.2.0")


class TestTaxBrainDynamicFields(TaxBrainFieldsTest):

    def test_set_fields(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['first_year'] = start_year
        self.parse_fields(start_year, fields,
                          Form=DynamicBehavioralInputsModelForm)

    def test_data_source_puf(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['first_year'] = start_year
        fields['data_source'] = 'PUF'
        model = self.parse_fields(start_year, fields,
                                  Form=DynamicBehavioralInputsModelForm,
                                  use_puf_not_cps=True)

        assert model.use_puf_not_cps

    def test_get_model_specs_with_errors(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['BE_sub'] = [-0.8]
        fields['BE_inc'] = [0.2]
        fields['first_year'] = start_year
        fields['data_source'] = 'PUF'
        model = self.parse_fields(start_year, fields,
                                  Form=DynamicBehavioralInputsModelForm,
                                  use_puf_not_cps=True)
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = model.get_model_specs()

        assert len(errors_warnings['behavior']['errors']) > 0
        assert len(errors_warnings['behavior']['warnings']) == 0
        assert len(errors_warnings['policy']['errors']) == 0
        assert len(errors_warnings['policy']['warnings']) == 0
