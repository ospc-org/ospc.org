from django.contrib import admin

# Register your models here.
from webapp.apps.register import models
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class SubscriberResource(resources.ModelResource):

    class Meta:
        model = models.Subscriber
        skip_unchanged = True
        report_skipped = True
        fields = ('id', 'email', 'active', 'subscribe_date')

class SubscriberAdmin(ImportExportModelAdmin):
    resource_class = SubscriberResource
    list_display = ('email', 'active', 'subscribe_date')

admin.site.register(models.Subscriber, SubscriberAdmin)
