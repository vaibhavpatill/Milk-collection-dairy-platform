
from django.contrib import admin
from .models import MilkProducer, MilkCollection, MilkRate

admin.site.register(MilkProducer)
admin.site.register(MilkCollection)
admin.site.register(MilkRate)
