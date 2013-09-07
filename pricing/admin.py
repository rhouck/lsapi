from pricing.models import Search_history
from django.contrib import admin



class Search_historyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    #def has_change_permission(self, request):
    #    return False
admin.site.register(Search_history, Search_historyAdmin)

