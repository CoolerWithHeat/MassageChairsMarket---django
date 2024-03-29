from django.contrib import admin
from .models import *

admin.site.register(MassageChair)
admin.site.register(ReviewResponse)
admin.site.register(ChairReview)
admin.site.register(ChairType)
admin.site.register(ChairFeature)
admin.site.register(Color_Options)
admin.site.register(UserReaction)


class ChairBrand(admin.ModelAdmin):
    list_display = ('brand_name', 'authorized_in')
admin.site.register(Brand, ChairBrand)