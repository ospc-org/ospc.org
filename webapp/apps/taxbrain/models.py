import re

from django.db import models
from django.core import validators
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import User

from uuidfield import UUIDField
from jsonfield import JSONField
import datetime

from helpers import rename_keys, PRE_TC_0130_RES_MAP

def convert_to_floats(tsi):
    """
    A helper function that tax all of the fields of a TaxSaveInputs model
    and converts them to floats, or list of floats
    """
    def numberfy_one(x):
        if isinstance(x, float):
            return x
        else:
            return float(x)

    def numberfy(x):
        if isinstance(x, list):
            return [numberfy_one(i) for i in x]
        else:
            return numberfy_one(x)

    attrs = vars(tsi)
    return { k:numberfy(v) for k,v in attrs.items() if v}


class CommaSeparatedField(models.CharField):
    default_validators = [validators.RegexValidator(regex='\d*\.\d+|\d+')]
    description = "A comma separated field that allows multiple floats."

    def __init__(self, verbose_name=None, name=None, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 200)
        super(CommaSeparatedField, self).__init__(verbose_name, name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CommaSeparatedField, self).deconstruct()
        if kwargs.get("max_length", None) == 1000:
            del kwargs['max_length']
        return name, path, args, kwargs


class SeparatedValuesField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, *args, **kwargs):
        self.token = kwargs.pop('token', ',')
        super(SeparatedValuesField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if not value: return
        if isinstance(value, list):
            return value
        return value.split(self.token)

    def get_db_prep_value(self, value, connection=None, prepared=False):
        if not value: return
        assert(isinstance(value, list) or isinstance(value, tuple))
        return self.token.join([unicode(s) for s in value])

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


class JSONReformTaxCalculator(models.Model):
    '''
    This class holds all of the text for a JSON-based reform input
    for TaxBrain. A TaxSavesInput Model will have a foreign key to
    an instance of this model if the user created the TaxBrain job
    through the JSON iput page.
    '''
    reform_text = models.TextField(blank=True, null=False)
    raw_reform_text = models.TextField(blank=True, null=False)
    assumption_text = models.TextField(blank=True, null=False)
    raw_assumption_text = models.TextField(blank=True, null=False)

class ErrorMessageTaxCalculator(models.Model):
    '''
    This class holds all of the text for an error message on
    TaxBrain. A TaxSavesInput Model will have a foreign key to
    an instance of this model if the user created the TaxBrain job
    that ends up failing and reporting this failure.
    '''
    text = models.CharField(blank=True, null=False, max_length=4000)


class TaxSaveInputs(models.Model):
    """
    This model contains all the parameters for the tax model and the tax
    result.

    For filing status fields:
    _0 = Single, _1 = Married filing Jointly, _2 = Married filing Separately,
    _3 = Head of Household (example: _SS_thd50_0 is the Single filing
    status for Income Threshold 1 in the Social Security Tax section.)
    The exception to this rule is for EITC, where:
    _0 = 0 Kids, _1 = 1 Kid, _2 = 2 Kids, & _3 = 3+ Kids
    """

    # Parameters used for Social Security.
    FICA_ss_trt = CommaSeparatedField(default=None, null=True, blank=True)
    FICA_mc_trt = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Income_c = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Income_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    SS_thd50_0 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd50_1 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd50_2 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd50_3 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd50_4 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd50_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    SS_percentage1 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_0 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_1 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_2 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_3 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_4 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    SS_percentage2 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Earnings_c = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Earnings_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameter for Additional Medicare tax
    AMEDT_rt   = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMEDT_ec_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Adjustments.
    ALD_StudentLoan_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_SelfEmploymentTax_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_SelfEmp_HealthIns_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_KEOGH_SEP_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_EarlyWithdraw_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Alimony_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_Child_c = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_Child_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ALD_Dependents_Elder_c = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_Elder_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ALD_Dependents_thd_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_thd_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_thd_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_thd_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_thd_4 = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Dependents_thd_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ALD_Investment_ec_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_InvInc_ec_base_code_active = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_InvInc_ec_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_EducatorExpenses_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_HSADeduction_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_IRAContributions_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_DomesticProduction_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Tuition_hc = CommaSeparatedField(default=None, blank=True, null=True)

    DependentCredit_Child_c = CommaSeparatedField(default=None, blank=True, null=True)
    DependentCredit_Nonchild_c = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_4 = CommaSeparatedField(default=None, blank=True, null=True)
    FilerCredit_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    FEI_ec_c = CommaSeparatedField(default=None, blank=True, null=True)
    FEI_ec_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Personal Exemptions.
    II_em = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_prt = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_em_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Standard Deductions.
    STD_Dep = CommaSeparatedField(default=None, blank=True, null=True)
    STD_0 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_1 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_2 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_3 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_4 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Personal Refundable Credit.
    II_credit_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_credit_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_credit_prt = CommaSeparatedField(default=None, blank=True, null=True)

    #Confirm for additional aged
    STD_Aged_0 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_1 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_2 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_3 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_4 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Itemized Deductions.
    ID_Medical_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_frt_add4aged = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Medical_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_InterestPaid_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_InterestPaid_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_InterestPaid_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_InterestPaid_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_InterestPaid_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_InterestPaid_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_Casualty_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_Miscellaneous_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_Charity_crt_all = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_crt_noncash = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_4 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_prt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_crt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_RealEstate_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_RealEstate_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_RealEstate_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_RealEstate_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_RealEstate_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_RealEstate_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_Charity_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_hc = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_trt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_crt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_em_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_em_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_em_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_em_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_em_4 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_Switch_0 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_1 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_2 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_3 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_4 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_5 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_6 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitCap_Switch_0 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_1 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_2 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_3 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_4 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_5 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitCap_Switch_6 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_c_4 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_AmountCap_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_AmountCap_rt_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_AmountCap_Switch_0 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_1 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_2 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_3 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_4 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_5 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_AmountCap_Switch_6 = models.CharField(default="True", blank=True, null=True, max_length=50)

    # Parameters used for Investment Tax Rates.
    CG_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_4 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CG_rt2    = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_4 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CG_rt3    = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_4 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CG_rt4    = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_rt1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt4 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_nodiff = CommaSeparatedField(default=None, blank=True, null=True)
    CG_ec = CommaSeparatedField(default=None, blank=True, null=True)
    CG_reinvest_ec_rt = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_rt = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_0 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_1 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_2 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_3 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_4 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Personal Income Tax Rate
    II_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt2    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt3    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt4    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt5    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt6    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt7    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk7_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt8 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_prt = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_4 = CommaSeparatedField(default=None, blank=True, null=True)
    II_credit_nr_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for the AMT.
    AMT_em_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_prt = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_Child_em_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_Child_em_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_Child_em_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_Child_em_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_Child_em_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_KT_c_Age = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_rt1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_rt2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_thd_MarriedS_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_thd_MarriedS_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_thd_MarriedS_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_em_pe_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_pe_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_pe_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt4 = CommaSeparatedField(default=None, blank=True, null=True)

    # Parameters used for Credits.
    EITC_rt_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_rt_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_rt_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_rt_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_prt_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_prt_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_prt_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_prt_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_MinEligAge = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_MinEligAge_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_MaxEligAge = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_MaxEligAge_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_ps_MarriedJ_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_MarriedJ_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_MarriedJ_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_MarriedJ_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_ps_MarriedJ_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_InvestIncome_c = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_InvestIncome_c_0 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_InvestIncome_c_1 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_InvestIncome_c_2 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_InvestIncome_c_3 = CommaSeparatedField(default=None, blank=True, null=True)
    EITC_InvestIncome_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    EITC_indiv = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_c = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CTC_prt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_4 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CTC_additional = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_refund_limit_rt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_refund_limit_payroll_rt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_c_under5_bonus = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_rt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_4 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CTC_new_prt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_c = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_c_under5_bonus = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_new_for_all = models.CharField(default="False", blank=True, null=True, max_length=50)
    DependentCredit_before_CTC = models.CharField(default="False", blank=True, null=True, max_length=50)
    ACTC_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ACTC_ChildNum = CommaSeparatedField(default=None, blank=True, null=True)
    ACTC_rt_bonus_under5family = CommaSeparatedField(default=None, blank=True, null=True)
    ACTC_Income_thd = CommaSeparatedField(default=None, blank=True, null=True)
    ACTC_Income_thd_cpi  = models.NullBooleanField(default=None, blank=True, null=True)
    DependentCredit_c = CommaSeparatedField(default=None, blank=True, null=True)
    LLC_Expense_c = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Single_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Single_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Single_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Single_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ETC_pe_Married_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Married_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Married_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ETC_pe_Married_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Child and dependent care phaseout
    CDCC_c = CommaSeparatedField(default=None, blank=True, null=True)
    CDCC_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CDCC_ps = CommaSeparatedField(default=None, blank=True, null=True)
    CDCC_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CDCC_crt = CommaSeparatedField(default=None, blank=True, null=True)
    CDCC_crt_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Pass through tax parameters
    PT_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt2    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt3    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt4    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk4_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt5    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk5_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt6    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk6_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt7    = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_0 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_1 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_2 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_3 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_4 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_brk7_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    PT_rt8 = CommaSeparatedField(default=None, blank=True, null=True)
    PT_EligibleRate_active = CommaSeparatedField(default=None, blank=True, null=True)
    PT_EligibleRate_passive = CommaSeparatedField(default=None, blank=True, null=True)
    PT_wages_active_income = models.CharField(default="False", blank=True, null=True, max_length=50)
    PT_top_stacking = models.CharField(default="True", blank=True, null=True, max_length=50)
    PT_exclusion_rt = CommaSeparatedField(default=None, blank=True, null=True)
    PT_exclusion_wage_limit = CommaSeparatedField(default=None, blank=True, null=True)
    PT_exclusion_wage_limit_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Fair Share Tax Parameters
    FST_AGI_trt = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_0 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_1 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_2 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_3 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_4 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_lo_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_0 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_1 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_2 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_3 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_4 = CommaSeparatedField(default=None, blank=True, null=True)
    FST_AGI_thd_hi_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    AGI_surtax_thd_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AGI_surtax_thd_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AGI_surtax_thd_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AGI_surtax_thd_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AGI_surtax_thd_4 = CommaSeparatedField(default=None, blank=True, null=True)
    AGI_surtax_thd_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AGI_surtax_trt = CommaSeparatedField(default=None, blank=True, null=True)

    LST = CommaSeparatedField(default=None, blank=True, null=True)

    CR_RetirementSavings_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_ForeignTax_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_ResidentialEnergy_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_GeneralBusiness_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_MinimumTax_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_AmOppRefundable_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_AmOppNonRefundable_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_SchR_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_OtherCredits_hc = CommaSeparatedField(default=None, blank=True, null=True)
    CR_Education_hc = CommaSeparatedField(default=None, blank=True, null=True)

    UBI1 = CommaSeparatedField(default=None, blank=True, null=True)
    UBI2 = CommaSeparatedField(default=None, blank=True, null=True)
    UBI3 = CommaSeparatedField(default=None, blank=True, null=True)
    UBI_ecrt = CommaSeparatedField(default=None, blank=True, null=True)

    # Boolean Checkbox Fields
    ALD_InvInc_ec_base_RyanBrady = models.CharField(default="False", blank=True, null=True, max_length=50)
    NIIT_PT_taxed = models.CharField(default="False", blank=True, null=True, max_length=50)
    CG_nodiff = models.CharField(default="False", blank=True, null=True, max_length=50)
    EITC_indiv = models.CharField(default="False", blank=True, null=True, max_length=50)
    CTC_new_refund_limited = models.CharField(default="False", blank=True, null=True, max_length=50)
    CTC_new_refund_limited_all_payroll = models.CharField(default="False", blank=True, null=True, max_length=50)
    II_no_em_nu18 = models.CharField(default="False", blank=True, null=True, max_length=50)

    # Inflation adjustments
    inflation = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)])
    inflation_years = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)])
    medical_inflation = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)])
    medical_years = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)])

    cpi_offset = CommaSeparatedField(default=None, blank=True, null=True)

    # Growth Assumptions
    factor_adjustment = CommaSeparatedField(default=None, blank=True, null=True)
    factor_target = CommaSeparatedField(default=None, blank=True, null=True)
    growth_choice = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)

    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)
    jobs_not_ready = SeparatedValuesField(blank=True, default=None, null=True)

    # Starting Year of the reform calculation
    first_year = models.IntegerField(default=None, null=True)

    # Record whether or not this was a quick calculation on a sample of data
    quick_calc = models.BooleanField(default=False)

    # generate fields from default param data
    # this may eventually be useful if we're able to ensure syncdb picks up
    # field changes and automatically create migrations
    """
    for param in TAXCALC_DEFAULT_PARAMS.values():

        for col_field in param.col_fields:
            exec(col_field.id + \
                " = CommaSeparatedField(default=None, null=True, blank=True)")

        if param.inflatable:
            exec(param.cpi_field.id + \
                " = models.NullBooleanField(default=None, blank=True, null=True)")

    """

    # Result
    _tax_result = JSONField(default=None, blank=True, null=True, db_column='tax_result')

    # JSON input text
    json_text = models.ForeignKey(JSONReformTaxCalculator, null=True, default=None, blank=True)

    # Error text
    error_text = models.ForeignKey(ErrorMessageTaxCalculator, null=True, default=None, blank=True)

    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))


    @property
    def tax_result(self):
        """
        If taxcalc version is greater than or equal to 0.13.0, return table
        If taxcalc version is less than 0.13.0, then rename keys to new names
        and then return table
        """
        outputurl = OutputUrl.objects.get(unique_inputs__pk=self.pk)
        taxcalc_vers = outputurl.taxcalc_vers
        taxcalc_vers = tuple(map(int, taxcalc_vers.split('.')))
        if taxcalc_vers >= (0, 13, 0):
            return self._tax_result
        else:
            return rename_keys(self._tax_result, PRE_TC_0130_RES_MAP)

    @tax_result.setter
    def tax_result(self, result):
        self._tax_result = result

    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class WorkerNodesCounter(models.Model):
    '''
    This class specifies a counter for which set of worker nodes we have
    just deployed a TaxBrain job to. It is a singleton class to enforce
    round robin behavior with multiple dynos running simultaneously. The
    database becomes the single source of truth for which set of nodes
    just got the last dispatch
    '''
    singleton_enforce = models.IntegerField(default=1, unique=True)
    current_offset = models.IntegerField(default=0)

class OutputUrl(models.Model):
    """
    This model creates a unique url for each calculation.
    """
    unique_inputs = models.ForeignKey(TaxSaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    # Expected Completion DateTime
    exp_comp_datetime = models.DateTimeField(default=datetime.datetime(2015, 1, 1))
    uuid = UUIDField(auto=True, default=None, null=True)
    taxcalc_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)
    webapp_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
