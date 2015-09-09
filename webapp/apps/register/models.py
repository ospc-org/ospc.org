from django.db import models
from django.core.mail import send_mail

import os
import uuid


# Create your models here.
class Subscriber(models.Model):
    email = models.EmailField(max_length=254)
    active = models.BooleanField(default=True)
    confirm_key = models.UUIDField(primary_key=False, default=uuid.uuid4)
    subscribe_date = models.DateField(auto_now_add=True)

    def send_subscribe_confirm_email(self):
        hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
        print(self.email)
        send_mail(
            subject="Thank you for joining the conversation on American tax policy",
            message = """Welcome!

            Thank you for registering with ospc.org. This is the best way to stay up to date on
            the latest news from the Open Source Policy Center. We also invite you to beta test
            the TaxBrain webapp.""",
            from_email = "Open Source Policy Center <mailing@ospc.org>",
            recipient_list = [self.email]
        )
