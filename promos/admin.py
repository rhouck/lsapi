from promos.models import Promo, Contest

from django.contrib import admin


class PromoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Promo, PromoAdmin)

class ContestAdmin(admin.ModelAdmin):
    pass
admin.site.register(Contest, ContestAdmin)