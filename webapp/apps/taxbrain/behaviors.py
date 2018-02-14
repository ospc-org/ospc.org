from django.db import models

import taxcalc

from distutils.version import LooseVersion
from .helpers import (rename_keys, reorder_lists, PRE_TC_0130_RES_MAP,
                      REORDER_LT_TC_0130_DIFF_LIST, DIFF_TABLE_IDs)
from ..constants import TAXCALC_VERS_RESULTS_BACKWARDS_INCOMPATIBLE
import param_formatters


class Resultable(models.Model):

    class Meta:
        abstract = True

    def get_tax_result(self, OutputUrlCls):
        """
        If taxcalc version is greater than or equal to 0.13.0, return table
        If taxcalc version is less than 0.13.0, then rename keys to new names
        and then return table
        """
        outputurl = OutputUrlCls.objects.get(unique_inputs__pk=self.pk)
        taxcalc_vers = outputurl.taxcalc_vers
        # only the older (pre 0.13.0) taxcalc versions are null
        if taxcalc_vers:
            taxcalc_vers = LooseVersion(taxcalc_vers)
        else:
            return rename_keys(self.tax_result, PRE_TC_0130_RES_MAP)

        # older PB versions stored commit reference too
        # e.g. taxcalc_vers = "0.9.0.d79abf"
        backwards_incompatible = LooseVersion(
            TAXCALC_VERS_RESULTS_BACKWARDS_INCOMPATIBLE
        )
        if taxcalc_vers >= backwards_incompatible:
            return self.tax_result
        else:
            renamed = rename_keys(self.tax_result, PRE_TC_0130_RES_MAP)
            return reorder_lists(renamed, REORDER_LT_TC_0130_DIFF_LIST,
                                 DIFF_TABLE_IDs)

class Fieldable(models.Model):

    class Meta:
        abstract = True

    def set_fields(self, upstream_obj):
        """
        Parse raw fields
            1. Only keep fields that user specifies
            2. Map TB names to TC names
            3. Do more specific type checking--in particular, check if
               field is the type that Tax-Calculator expects from this param
        """
        default_data = upstream_obj.default_data(start_year=self.start_year,
                                                   metadata=True)
        fields = param_formatters.parse_fields(self.raw_fields, default_data)
        param_formatters.switch_fixup(fields, self)
        self.fields = fields

    def get_model_specs(self):
        """
        Stub to remind that this part of the API is needed
        """
        raise NotImplementedError()
