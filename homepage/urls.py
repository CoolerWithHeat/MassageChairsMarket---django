from django.contrib import admin
from django.urls import path
from soothestore.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomePage),
    path('FindProduct/', SearchPage),
    path('Buy/<int:product_id>/', Buy),
    path('FAQ/', FAQ),
    path('Cart/', Cart),
    path('VerifyCart/', CheckCart.as_view()),
    path('RecordReview/<int:chair_id>/', ChairReviewCreateAPIView.as_view()),
    path('GetReview/<int:product_id>/', ProductReviewsEndpoint.as_view()),
    path('RecordUserReaction/<int:review_id>/', UserReactionCreateView.as_view()),
    path('GetProduct/<int:product_ID>/', MassageChairDetailView.as_view()),
]