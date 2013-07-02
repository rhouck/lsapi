from sales.models import Platform, Customer, Contract, Open

from django.contrib import admin


class ContractAdmin(admin.ModelAdmin):

    list_display = ('purch_date', 'ex_fare', 'get_exp_date', 'get_holding_price', 'get_locked_fare', 'outstanding')
    """
    fieldsets = [
                (None, {'fields': ('platform', 'customer', 'purch_date', 'exp_date', 'option_price', 'locked_fare', 'ex_fare')}),
                ]
    """

    #list_filter = ['get_exp_date']
    #date_hierarchy = 'get_exp_date'

    def get_exp_date(self, obj):
        return (obj.search.exp_date)
    get_exp_date.short_description = 'expiration date'


    def get_holding_price(self, obj):
        return (obj.search.holding_price)
    get_holding_price.short_description = 'holding price'

    def get_locked_fare(self, obj):
        return (obj.search.locked_fare)
    get_locked_fare.short_description = 'locked fare'

    def has_add_permission(self, request):
        return False
    #def has_change_permission(self, request):
    #    return False

admin.site.register(Contract, ContractAdmin)


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name')
    inlines = [ContractInline]
admin.site.register(Customer, CustomerAdmin)


class PlatformAdmin(admin.ModelAdmin):
    list_display = ('org_name', 'web_site')
    inlines = [ContractInline]
admin.site.register(Platform, PlatformAdmin)


class OpenAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

    #def has_change_permission(self, request):
    #    return False
admin.site.register(Open, OpenAdmin)

