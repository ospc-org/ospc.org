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

#from .helpers import TAXCALC_DEFAULT_PARAMS


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
    SS_thd50_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    SS_percentage1 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_0 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_1 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_2 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_3 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_thd85_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    SS_percentage2 = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Earnings_c = CommaSeparatedField(default=None, null=True, blank=True)
    SS_Earnings_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameter for Additional Medicare tax
    AMED_trt   = CommaSeparatedField(default=None, blank=True, null=True)
    AMED_thd_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMED_thd_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMED_thd_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMED_thd_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMED_thd_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Adjustments.
    ALD_StudentLoan_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_SelfEmploymentTax_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_SelfEmp_HealthIns_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_KEOGH_SEP_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_EarlyWithdraw_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ALD_Alimony_HC = CommaSeparatedField(default=None, blank=True, null=True)
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
    STD_0 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_1 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_2 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_3 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    #Confirm for additional aged
    STD_Aged_0 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_1 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_2 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_3 = CommaSeparatedField(default=None, blank=True, null=True)
    STD_Aged_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Itemized Deductions.
    ID_Medical_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Casualty_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Miscellaneous_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_crt_Cash = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_crt_Asset = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    ID_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ID_prt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_crt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_StateLocalTax_HC = CommaSeparatedField(default=None, blank=True, null=True)
    ID_Charity_frt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_trt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_crt = CommaSeparatedField(default=None, blank=True, null=True)
    ID_BenefitSurtax_Switch_0 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_1 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_2 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_3 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_4 = models.CharField(default="True", blank=True, null=True, max_length=50)
    ID_BenefitSurtax_Switch_5 = models.CharField(default="True", blank=True, null=True, max_length=50)

    # Parameters used for Investment Tax Rates.
    CG_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CG_rt2    = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CG_thd2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CG_rt3    = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    Dividend_rt2  = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    Dividend_rt3  = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    Dividend_thd3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    NIIT_trt = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_0 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_1 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_2 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_3 = CommaSeparatedField(default=None, blank=True, null=True)
    NIIT_thd_cpi = models.NullBooleanField(default=None, blank=True, null=True)

    # Parameters used for Personal Income Tax Rate
    II_rt1    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt2    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt3    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk3_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt4    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk4_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt5    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk5_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt6    = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_0 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_1 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_2 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_3 = CommaSeparatedField(default=None, blank=True, null=True)
    II_brk6_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    II_rt7    = CommaSeparatedField(default=None, blank=True, null=True)

    # Parameters used for the AMT.
    AMT_em_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_prt = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_em_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_trt1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_trt2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_tthd = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_tthd_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd1_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd1_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd1_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd1_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd1_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd2_0 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd2_1 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd2_2 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd2_3 = CommaSeparatedField(default=None, blank=True, null=True)
    AMT_CG_thd2_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    AMT_CG_rt3 = CommaSeparatedField(default=None, blank=True, null=True)

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
    CTC_c = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_c_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    CTC_prt = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_0 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_1 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_2 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_3 = CommaSeparatedField(default=None, blank=True, null=True)
    CTC_ps_cpi = models.NullBooleanField(default=None, blank=True, null=True)
    ACTC_rt = CommaSeparatedField(default=None, blank=True, null=True)
    ACTC_ChildNum = CommaSeparatedField(default=None, blank=True, null=True)

    # Inflation adjustments
    inflation = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)])
    inflation_years = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)])
    medical_inflation = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0.000), MaxValueValidator(1.000)])
    medical_years = models.FloatField(default=None, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)])

    # Behavioral Effects
    BE_inc = CommaSeparatedField(default=None, blank=True, null=True)
    BE_sub = CommaSeparatedField(default=None, blank=True, null=True)
    BE_cg_per = CommaSeparatedField(default=None, blank=True, null=True)
    BE_cg_trn = CommaSeparatedField(default=None, blank=True, null=True)

    # Growth Assumptions
    factor_adjustment = CommaSeparatedField(default=None, blank=True, null=True)
    factor_target = CommaSeparatedField(default=None, blank=True, null=True)
    growth_choice = models.CharField(blank=True, default=None, null=True,
                                     max_length=50)


    # Job IDs when running a job
    job_ids = SeparatedValuesField(blank=True, default=None, null=True)

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
    tax_result = JSONField(default=None, blank=True, null=True)
    # Creation DateTime
    creation_date = models.DateTimeField(default=datetime.datetime(2015, 1, 1))


    class Meta:
        permissions = (
            ("view_inputs", "Allowed to view Taxbrain."),
        )


class OutputUrl(models.Model):
    """
    This model creates a unique url for each calculation.
    """
    unique_inputs = models.ForeignKey(TaxSaveInputs, default=None)
    user = models.ForeignKey(User, null=True, default=None)
    model_pk = models.IntegerField(default=None, null=True)
    uuid = UUIDField(auto=True, default=None, null=True)
    taxcalc_vers = models.CharField(blank=True, default=None, null=True,
        max_length=50)

    def get_absolute_url(self):
        kwargs = {
            'pk': self.pk
        }
        return reverse('output_detail', kwargs=kwargs)
