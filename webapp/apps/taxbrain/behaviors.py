"""
This module provides a set of mix-ins to be used throughout PolicyBrain models.
To read more about Django model mix-ins, check out the following links:
https://docs.djangoproject.com/en/2.0/topics/db/models/#abstract-base-classes
http://blog.kevinastone.com/django-model-behaviors.html
"""

from django.db import models

import taxcalc

from distutils.version import LooseVersion
from .helpers import (rename_keys, reorder_lists, PRE_TC_0130_RES_MAP,
                      REORDER_LT_TC_0130_DIFF_LIST, DIFF_TABLE_IDs)
from ..constants import TAXCALC_VERS_RESULTS_BACKWARDS_INCOMPATIBLE
from . import param_formatters

class Resultable(models.Model):
    """
    Mix-in to provide logic around retrieving model results.
    """

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
    """
    Mix-in for providing logic around formatting raw GUI input fields
    """

    class Meta:
        abstract = True

    def set_fields(self, upstream_obj, nonparam_fields=None):
        """
        Parse raw fields
            1. Only keep fields that user specifies
            2. Map TB names to TC names
            3. Do more specific type checking--in particular, check if
               field is the type that Tax-Calculator expects from this param
        """
        if isinstance(upstream_obj, taxcalc.Policy):
            pol = taxcalc.Policy()
            pol.set_year(start_year)
            default_data = pol.metadata()
        else: #isinstance(upstream_obj, taxcalc.Behavior):
            default_data = taxcalc.Behavior()._vals

        if self.raw_input_fields is None:
            self.raw_input_fields = {}
            for field in self._meta.fields:
                if (getattr(self, field.attname, None) and
                    field.name not in nonparam_fields):
                    raw_val = getattr(self, field.attname)
                    if field.name.endswith("cpi") and isinstance(raw_val, bool):
                        raw_val = str(raw_val)
                    self.raw_input_fields[field.name] = raw_val

        input_fields, failed_lookups = param_formatters.parse_fields(
            self.raw_input_fields,
            default_data
        )

        if failed_lookups:
            # distinct elements
            potential_failed_lookups = set(failed_lookups)
            # only keep parameters that used to be in the upstream package
            set_failed_lookups = potential_failed_lookups - nonparam_fields
            if self.deprecated_fields is None:
                self.deprecated_fields = []
            # drop parameters that we already know are deprecated
            set_failed_lookups.difference_update(self.deprecated_fields)
            self.deprecated_fields += list(set_failed_lookups)

        self.input_fields = input_fields

    def pop_extra_errors(self, errors_warnings):
        """
        Removes errors on extra parameters
        """
        for project in errors_warnings:
            for action in ['warnings', 'errors']:
                params = list(errors_warnings[project][action].keys())
                for param in params:
                    if param not in self.raw_input_fields:
                        errors_warnings[project][action].pop(param)


    def get_model_specs(self):
        """
        Stub to remind that this part of the API is needed
        """
        raise NotImplementedError()


class DataSourceable(models.Model):
    """
    Mix-in for providing data_source field and methods that access it
    """

    class Meta:
        abstract = True

    # data source for model
    data_source = models.CharField(default="PUF", blank=True, null=True, max_length=20)

    @property
    def use_puf_not_cps(self):
        # which file to use, front-end not yet implemented
        if self.data_source == 'PUF':
            return True
        else:
            return False


class Hostnameable(models.Model):
    """
    Mix-in for providing functionality around hostnames
    """
    class Meta:
        abstract = True

    def check_hostnames(self, current_hostnames):
        """
        Make sure all hostnames are valid before posting to/getting data from
        them
        """
        if self.jobs_not_ready is None:
            return True
        for id in self.jobs_not_ready:
            hn = id.split('#')[1]
            if hn not in current_hostnames:
                return False
        return True
