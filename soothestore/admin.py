from django.contrib import admin
from .models import *

admin.site.register(MassageChair)
admin.site.register(ReviewResponse)
admin.site.register(ChairReview)
admin.site.register(ChairType)
admin.site.register(ChairFeature)
admin.site.register(Color_Options)
admin.site.register(UserReaction)
admin.site.register(Additional_Images)
admin.site.register(VideoShowcase)
admin.site.register(discount_code)
admin.site.register(SubscribedCustomers)
admin.site.register(ShippingInformation)
admin.site.register(Payment_Session)
admin.site.register(product_track)
admin.site.register(CompanyContactInformation)
admin.site.register(CustomerInquiry)
admin.site.register(FAQ)
admin.site.register(ProductMeta)

class ChairBrand(admin.ModelAdmin):
    list_display = ('brand_name', 'authorized_in')
    
admin.site.register(Brand, ChairBrand)