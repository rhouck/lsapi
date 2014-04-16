from promos.models import Promo, Contest, Submission

from django.contrib import admin


class PromoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Promo, PromoAdmin)

class ContestAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contest, ContestAdmin)

class SubmissionAdmin(admin.ModelAdmin):
    pass
admin.site.register(Submission, SubmissionAdmin)