from analysis.models import Search_history, Cash_reserve, Additional_capacity
from django.contrib import admin



class Search_historyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    #def has_change_permission(self, request):
    #    return False
admin.site.register(Search_history, Search_historyAdmin)


class Cash_reserveAdmin(admin.ModelAdmin):
    # diable add permissions only after initializing starting cash level
    def has_add_permission(self, request):
        return True
    #def has_change_permission(self, request):
    #    return False
admin.site.register(Cash_reserve, Cash_reserveAdmin)


class Additional_capacityAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

    #def has_change_permission(self, request):
    #    return False
admin.site.register(Additional_capacity, Additional_capacityAdmin)


