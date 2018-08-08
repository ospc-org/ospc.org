import os
import pytest
import numpy as np
from django.utils import timezone

from ..taxbrain.models import (JSONReformTaxCalculator,
                               OutputUrl, TaxSaveInputs)
from ..dynamic.models import (DynamicBehaviorSaveInputs,
                              DynamicElasticitySaveInputs)
from ..btax.models import BTaxSaveInputs
from .utils import get_taxbrain_model, stringify_fields
from ..taxbrain.forms import TaxBrainForm

START_YEAR = 2016

CURDIR = os.path.abspath(os.path.dirname(__file__))



@pytest.mark.usefixtures("skelaton_res_lt_0130",
                         "skelaton_res_gt_0130")
@pytest.mark.django_db
class TaxBrainTableResults(object):

    def tc_table_backcompat(self, fields, bef, aft, Form=TaxBrainForm,
                            UrlModel=OutputUrl, taxcalc_vers="0.10.2.abc",
                            webapp_vers="1.1.1"):
        unique_url = get_taxbrain_model(fields,
                                        taxcalc_vers=taxcalc_vers,
                                        webapp_vers=webapp_vers,
                                        Form=Form, UrlModel=UrlModel)

        model = unique_url.unique_inputs
        model.tax_result = bef
        model.creation_date = timezone.now()
        model.save()

        np.testing.assert_equal(model.get_tax_result(),
                                aft)


@pytest.mark.django_db
class TaxBrainFieldsTest(object):

    def parse_fields(self, start_year, fields, Form=TaxBrainForm,
                     exp_result=None, use_puf_not_cps=True):
        start_year = 2017
        fields = stringify_fields(fields)
        form = Form(start_year, use_puf_not_cps, fields)

        # returns model object but does not save to the database
        model = form.save(commit=False)

        # parse fields--map to package name and cast input strings to python
        # vals as specified by upstream package
        model.set_fields()
        model.save()
        # get formatted model specifications
        model.get_model_specs()
        # do some kind of check here using `exp_result`

        return model
