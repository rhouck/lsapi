from pricing.models import Searches, ExpiredSearchPriceCheck
from django.contrib import admin



class SearchesAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    #def has_change_permission(self, request):
    #    return False
admin.site.register(Searches, SearchesAdmin)

class ExpiredSearchPriceCheckAdmin(admin.ModelAdmin):
    list_display = ('run_date',)
    #def has_add_permission(self, request):
    #    return False
    #def has_change_permission(self, request):
    #    return False
admin.site.register(ExpiredSearchPriceCheck, ExpiredSearchPriceCheckAdmin)

