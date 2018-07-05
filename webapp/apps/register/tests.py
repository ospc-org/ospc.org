from django.test import TestCase

import pytest

from django.test import Client
from django.core.urlresolvers import reverse

from webapp.apps.register.models import Subscriber
#run this with `py.test --pdb -s -m register`
#actually no. `py.test -q webapp/apps/register/tests.py`

@pytest.mark.register
class RegisterTestCase(TestCase):
    def test_initial_subscribe(self):
        subscriber = Subscriber.objects.create(
            email = 'test@example.com',
        )
        self.assertFalse(subscriber.active)

    def test_post_registration_email(self):
        c = Client()
        response = c.post(reverse('about'), {'email': 'afarrell+test1@continuum.io'})
        subscriber = Subscriber.objects.get(email = 'afarrell+test1@continuum.io')
        self.assertFalse(subscriber.active)

    def test_confirm_link_correct(self):
        subscriber = Subscriber.objects.create(
            email = 'test@example.com',
        )
        self.assertEqual(subscriber.confirm_url("http://ospc-taxes.org"),
          "http://ospc-taxes.org/register/?k={}".format(subscriber.confirm_key)
        )

    #Tests to write:
    # User enters in a username that already exists, then changes it and resubmits
    # User enters an email that is the same as an existing email.

#    def test_patching_works(self):
#        with patch('django.core.mail.send_mail') as mocked_send_mail:
#            from django.core.mail import send_mail
#            send_mail(subject="foo", message="bar", from_email="andrew <amfarrell@mit.edu>",
#                recipient_list = ['farrell <afarrell@mit.edu>',])
#            self.assertTrue(mocked_send_mail.called)
#
#    def test_mail_is_sent(self):
#        with patch('django.core.mail.send_mail') as mocked_send_mail:
#            from webapp.apps.register.models import Subscriber
#            subscriber = Subscriber.objects.create(
#                email = 'test@example.com',
#            )
#            subscriber.save()
#            self.assertFalse(subscriber.active)
#            self.assertTrue(mocked_send_mail.called)
#            self.assertEqual(mocked_send_mail.call_args['recipient_list'], 'test@example.com')
#            self.assertIn(mocked_send_mail.call_args['message'], subscriber.confirm_key)




