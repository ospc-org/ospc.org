from __future__ import print_function
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
import mock
import os
os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute
import taxcalc
from taxcalc import Policy
from .utils import *

START_YEAR = 2016


class DynamicOGUSAViewsTests(TestCase):
    ''' Test the ogusa dynamic views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')


    def test_ogusa_different_start_years(self):
        self.client.login(username='temporary', password='temporary')
        # Do the microsim
        start_year = 2015
        reform = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(start_year), 'csrfmiddlewaretoken': 'abc123'}

        # Do a 2015 microsim
        micro_2015 = do_micro_sim(self.client, reform)

        # Do the ogusa simulation based on this microsim
        ogusa_reform = {u'frisch': [u'0.42']}
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform, start_year)
        orig_micro_model_num = micro_2015.url[-2:-1]

        # Do a 2016 microsim
        micro_2016 = do_micro_sim(self.client, reform)
        # Do the ogusa simulation based on this microsim
        ogusa_reform = {u'frisch': [u'0.43']}
        ogusa_response2 = do_ogusa_sim(self.client, micro_2016, ogusa_reform, start_year)
