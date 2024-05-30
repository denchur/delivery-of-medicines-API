from django.contrib import admin
from .models import *

class MedicamentsInOrdersAdmin(admin.TabularInline):
    model = MedicamentsInOrders
    extra = 1
    min_num = 1

class OrderAdmin(admin.ModelAdmin):
    inlines = [
        MedicamentsInOrdersAdmin,
    ]

admin.site.register(Curier)
admin.site.register(SupportedPharmacy)
admin.site.register(Order, OrderAdmin)
admin.site.register(SupportedСities)
admin.site.register(Medication)
admin.site.register(MedicamentsInOrders)
admin.site.register(RefuceOrdersCurier)
