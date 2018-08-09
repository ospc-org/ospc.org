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
            reform_parameters=TestTaxBrainJSONReformModel.test_string,
            reform_inputs_file=TestTaxBrainJSONReformModel.test_string,
            assumption_parameters=TestTaxBrainJSONReformModel.test_string,
            assumption_inputs_file=TestTaxBrainJSONReformModel.test_string
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

    def test_old_runs(self):
        """
        Test that the fields JSON objects can be generated dyanamically
        """
        start_year = 2017
        tsi = TaxSaveInputs(
            ID_AmountCap_Switch_0='True',
            FICA_ss_trt='0.10',
            STD_cpi='True',
            SS_Earnings_c_cpi=True,
            first_year=start_year
        )
        tsi.save()
        tsi.set_fields()
        assert tsi.gui_field_inputs['_FICA_ss_trt'] == [0.10]
        assert tsi.gui_field_inputs['_STD_cpi']
        assert tsi.gui_field_inputs['_SS_Earnings_c_cpi']
        assert tsi.gui_field_inputs['_ID_AmountCap_Switch_medical'] == [True]

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
