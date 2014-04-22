from sales.models import Platform, Customer, Contract, Staging, Demo, Alerts, AlertsCheck

from django.contrib import admin

from django.http import HttpResponse

class ContractAdmin(admin.ModelAdmin):

    list_display = ('customer', 'search', 'get_exp_date', 'ex_fare', 'outstanding', 'staged')

    #fieldsets = [
    #            (None, {'fields': ('platform', 'customer', 'purch_date', 'exp_date', 'option_price', 'locked_fare', 'ex_fare')}),
    #            ]


    #list_filter = ['get_exp_date']
    #date_hierarchy = 'get_exp_date'

    def get_exp_date(self, obj):
        return (obj.search.exp_date.strftime("%B %d, %Y"))
    get_exp_date.short_description = 'Date / time expiration'
    
    """
    def get_holding_price(self, obj):
        return (obj.search.holding_price)
    get_holding_price.short_description = 'holding price'

    def get_locked_fare(self, obj):
        return (obj.search.locked_fare)
    get_locked_fare.short_description = 'locked fare'
    """
    def has_add_permission(self, request):
        return False
    #def has_change_permission(self, request):
    #    return False

admin.site.register(Contract, ContractAdmin)


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0



class DemoAdmin(admin.ModelAdmin):

    list_display = ('purch_date', 'get_exp_date', 'get_holding_price', 'get_locked_fare', 'outstanding')

    
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

admin.site.register(Demo, DemoAdmin)


class DemoInline(admin.TabularInline):
    model = Demo
    extra = 0



class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'last_name', 'first_name', 'platform',)
    inlines = [ContractInline]
admin.site.register(Customer, CustomerAdmin)


class CustomerInline(admin.TabularInline):
    model = Customer
    extra = 0
    #inlines = [ContractInline]

class PlatformAdmin(admin.ModelAdmin):
    list_display = ('org_name', 'web_site')
    inlines = [CustomerInline]
admin.site.register(Platform, PlatformAdmin)


class StagingAdmin(admin.ModelAdmin):
    list_display = ('contract',)
    def has_add_permission(self, request):
        return False
admin.site.register(Staging, StagingAdmin)


class AlertsAdmin(admin.ModelAdmin):
    pass
admin.site.register(Alerts, AlertsAdmin)

class AlertsCheckAdmin(admin.ModelAdmin):
    pass
admin.site.register(AlertsCheck, AlertsCheckAdmin)