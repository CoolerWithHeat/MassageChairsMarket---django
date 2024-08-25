from rest_framework import serializers
from .models import *


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'brand_name', 'authorized_in', 'order_tracking_available', 'brand_logo']

class ChairFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChairFeature
        fields = ['id', 'called', 'feature_description', 'feature_showcase', 'feature_side']

class ColorOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color_Options
        fields = ['id', 'color_name', 'color_code', 'image']

class DiscountCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = discount_code
        fields = '__all__' 
    
class ProductMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductMeta
        fields = '__all__' 


class CustomerInquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerInquiry
        fields = ['id', 'customer_email', 'customer_name', 'customer_question', 'asked_date', 'handled']

class CompanyContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyContactInformation
        fields = ['phone_number', 'company_email']

class MassageChairSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    available_colors = ColorOptionsSerializer(many=True)
    color_options = serializers.SerializerMethodField()
    additional_images = serializers.SerializerMethodField()
    additional_images_admin = serializers.SerializerMethodField()
    chair_features = serializers.SerializerMethodField()
    video_demonstrations = serializers.SerializerMethodField()

    class Meta:
        model = MassageChair
        fields = ['id', 'title', 'brand', 'price', 'description', 'available_colors', 'purchased', 'rating', 'posted', 'color_options', 'additional_images', 'chair_features', 'video_demonstrations', 'discount_amount', 'additional_images_admin', 'has_reviewers']

    def get_color_options(self, obj):
        return [[color.color_name, color.color_code, color.image.url] for color in obj.available_colors.all()]

    def get_chair_features(self, obj):
        return [{'id': feature.id, 'called': feature.called, 'showcase_side': feature.feature_side, 'information': feature.feature_description, 'image':feature.feature_showcase.url} for feature in obj.features.all()]

    def get_video_demonstrations(self, obj):
        return [{'id': demo.id, 'video_id':demo.video_id, 'video_side':demo.video_side, 'platform': demo.video_platform, 'information': demo.showcase_text} for demo in obj.video_demo.all()]

    def get_additional_images(self, obj):
        return [images.image.url for images in obj.additional_images.all()]
    
    def get_additional_images_admin(self, obj):
        return [{'id':images.id, 'image':images.image.url} for images in obj.additional_images.all()]

class FAQ_serializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'priority']

class ReviewResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewResponse
        fields = ['poster', 'response_text', 'responded_date']

class ChairReviewSerializer(serializers.ModelSerializer):
    replies = ReviewResponseSerializer(many=True, read_only=True)
    is_the_first = serializers.SerializerMethodField()
    posted_for = MassageChairSerializer()
    class Meta:
        model = ChairReview
        fields = ['id', 'posted_for', 'poster', 'poster_location', 'customer_rate', 'review_text', 'posted_date', 'replies', 'is_the_first']
    
    def get_is_the_first(self, obj):
        first_review = ChairReview.objects.count()
        return first_review == 1
    
class AdminReviewsSerializer(serializers.ModelSerializer):
    posted_for = MassageChairSerializer()
    class Meta:
        model = ChairReview
        fields = ['id', 'posted_for', 'poster', 'poster_location', 'customer_rate', 'review_text', 'posted_date']

class UserReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReaction
        fields = ['to_review', 'user_identity', 'action']

    def validate_action(self, value):
        if value not in [UserReaction.LIKE, UserReaction.DISLIKE]:
            raise serializers.ValidationError("Invalid action. Must be 'like' or 'dislike'.")
        return value


class ShippingInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingInformation
        fields = (
            'id', 'firstname', 'lastname', 'apartment_suite',
            'address', 'country', 'zipcode', 'city', 'state', 'phone_number',
        )

class PaymentSessionSerializer(serializers.ModelSerializer):
    shipping_address = ShippingInformationSerializer()

    class Meta:
        model = Payment_Session
        fields = (
            'id', 'order_number', 'session', 'completed', 'verified_cart',
            'shipping_address', 'created', 'expected_amount', 'associated_email', 'first_time_view', 'order_closed',
        )

class TrackingSerializer(serializers.ModelSerializer):
    of_order = PaymentSessionSerializer()
    tracking_product = MassageChairSerializer()
    class Meta:
        model = product_track
        fields = ['id', 'of_order', 'tracking_product', 'order_number_provided_by_brand', 'tracking_stage']