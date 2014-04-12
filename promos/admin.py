from promos.models import Promo

from django.contrib import admin


class PromoAdmin(admin.ModelAdmin):
    pass
admin.site.register(Promo, PromoAdmin)