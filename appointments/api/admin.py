from django.contrib import admin
from .models import Provider, Patient, Topic, Appointment

admin.site.register(Provider)
admin.site.register(Patient)
admin.site.register(Topic)
admin.site.register(Appointment)