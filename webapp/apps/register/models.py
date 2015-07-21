from django.db import models
from django.core.mail import send_mail

import os
import urllib
import uuid


# Create your models here.
class Subscriber(models.Model):
    email = models.EmailField(max_length=254)
    active = models.BooleanField(default=False)
    confirm_key = models.UUIDField(primary_key=False, default=uuid.uuid4)
    subscribe_date = models.DateField(auto_now_add=True)

    def confirm_url(self, hostname, secure = False):
      return "{host}{path}?{params}".format(
            host = hostname,
            path = reverse('register_user'),
            params = urllib.urlencode({'k': self.confirm_key})
        )


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.urlresolvers import reverse

@receiver(post_save, sender=Subscriber)
def send_subscribe_confirm_email(sender, instance, **kwargs):
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    send_mail(subject="Thank you for joining the conversation on American tax policy",
        message = """Welcome!

        Thank you for registering with ospc.org. This is the best way to stay up to date on
        the latest news from the Open Source Policy Center. We also invite you to beta test
        the TaxBrain webapp.


        Please visit {url} to confirm your subscription""".format(url = instance.confirm_url(hostname)),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [instance.email,])
