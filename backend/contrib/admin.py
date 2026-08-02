from django.contrib import admin
from .models import ArchitectureSnapshot, Recommendation, PrDraft

admin.site.register(ArchitectureSnapshot)
admin.site.register(Recommendation)
admin.site.register(PrDraft)
