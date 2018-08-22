import json

import pytest

from ..models import TaxSaveInputs, TaxBrainRun
from ..forms import TaxBrainForm
from ...test_assets.test_models import TaxBrainFieldsTest


@pytest.mark.django_db
class TestTaxBrainJSONReformModel(object):
    """Test taxbrain JSONReformTaxCalculator."""

    test_string = "[" + ", ".join(["1" for x in range(100000)]) + "]"

    def test_create_reforms(self):
        self.reforms = TaxSaveInputs.objects.create(
            upstream_parameters=TestTaxBrainJSONReformModel.test_string,
            inputs_file=TestTaxBrainJSONReformModel.test_string
        )

    def test_get_errors_warnings_post_PB_160(self):
        """
        Test get old errors/warnings
        """
        post_PB_160 = {
            'project': {
                'errors': {'1900': 'test'},
                'warnings': {'1770': 'test2'}
            }
        }
        reform = TaxSaveInputs.objects.create(
            errors_warnings_text=post_PB_160
        )
        assert reform.errors_warnings_text == post_PB_160


class TestTaxBrainStaticFields(TaxBrainFieldsTest):

    def test_set_fields(self, test_coverage_gui_fields):
        start_year = 2017
        fields = test_coverage_gui_fields.copy()
        fields['first_year'] = start_year

        self.parse_fields(start_year, fields, Form=TaxBrainForm)

    def test_deprecated_fields(self):
        """
        Test that deprecated fields are added correctly
        """
        start_year = 2017
        tsi = TaxSaveInputs(
            raw_gui_field_inputs={
                'FICA_ss_trt': '0.10',
                'ID_BenefitSurtax_Switch_0': 'True',
                'STD_cpi': 'True',
                'deprecated_param': '1000'
            },
            first_year=start_year
        )
        tsi.set_fields()
        assert tsi.deprecated_fields == ['deprecated_param']
        tsi.raw_gui_field_inputs['yet_another_deprecated_param'] = '1001'
        tsi.set_fields()
        assert tsi.deprecated_fields == ['deprecated_param',
                                         'yet_another_deprecated_param']
        assert tsi.raw_gui_field_inputs['deprecated_param'] == '1000'
        assert (
            tsi.raw_gui_field_inputs['yet_another_deprecated_param'] == '1001')
        assert 'deprecated_param' not in tsi.gui_field_inputs
        assert 'yet_another_deprecated_param' not in tsi.gui_field_inputs

    def test_data_source_puf(self, test_coverage_gui_fields):
        start_year = 2017
        fields = test_coverage_gui_fields.copy()
        fields['first_year'] = start_year
        fields['data_source'] = 'PUF'
        model = self.parse_fields(start_year, fields,
                                  use_puf_not_cps=True)

        assert model.use_puf_not_cps

    def test_data_source_cps(self, test_coverage_gui_fields):
        start_year = 2017
        fields = test_coverage_gui_fields.copy()
        fields['first_year'] = start_year
        fields['data_source'] = 'CPS'
        model = self.parse_fields(start_year, fields,
                                  use_puf_not_cps=False)

        assert not model.use_puf_not_cps

    def test_set_fields(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['first_year'] = start_year
        self.parse_fields(start_year, fields)

    def test_data_source_puf(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['first_year'] = start_year
        fields['data_source'] = 'PUF'
        model = self.parse_fields(start_year, fields, use_puf_not_cps=True)

        assert model.use_puf_not_cps

    def test_get_model_specs_with_errors(self, test_coverage_behavioral_gui_fields):
        start_year = 2017
        fields = test_coverage_behavioral_gui_fields.copy()
        fields['BE_sub'] = [-0.8]
        fields['BE_inc'] = [0.2]
        fields['first_year'] = start_year
        fields['data_source'] = 'PUF'
        model = self.parse_fields(start_year, fields, use_puf_not_cps=True)
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = model.get_model_specs()

        assert len(errors_warnings['behavior']['errors']) > 0
        assert len(errors_warnings['behavior']['warnings']) == 0
        assert len(errors_warnings['policy']['errors']) == 0
        assert len(errors_warnings['policy']['warnings']) == 0
