from rest_framework import serializers
from .models import *


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'brand_name', 'authorized_in']

class ChairFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChairFeature
        fields = ['id', 'called']

class ColorOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color_Options
        fields = ['id', 'color_name', 'color_code', 'image']

class MassageChairSerializer(serializers.ModelSerializer):
    brand = BrandSerializer()
    available_colors = ColorOptionsSerializer(many=True)
    features = ChairFeatureSerializer(many=True)
    color_options = serializers.SerializerMethodField()
    chair_features = serializers.SerializerMethodField()
    
    class Meta:
        model = MassageChair
        fields = ['id', 'title', 'brand', 'price', 'description', 'available_colors', 'features', 'purchased', 'rating', 'posted', 'color_options', 'chair_features', 'discount_amount']

    def get_color_options(self, obj):
        return [[color.color_name, color.color_code, color.image.url] for color in obj.available_colors.all()]

    def get_chair_features(self, obj):
        return [feature.called for feature in obj.features.all()]

class ReviewResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewResponse
        fields = ['poster', 'response_text', 'responded_date']

class ChairReviewSerializer(serializers.ModelSerializer):
    replies = ReviewResponseSerializer(many=True, read_only=True)
    is_the_first = serializers.SerializerMethodField()

    class Meta:
        model = ChairReview
        fields = ['id', 'posted_for', 'poster', 'poster_location', 'customer_rate', 'review_text', 'posted_date', 'replies', 'is_the_first']
    
    def get_is_the_first(self, obj):
        first_review = ChairReview.objects.count()
        return first_review == 1

class UserReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReaction
        fields = ['to_review', 'user_identity', 'action']

    def validate_action(self, value):
        if value not in [UserReaction.LIKE, UserReaction.DISLIKE]:
            raise serializers.ValidationError("Invalid action. Must be 'like' or 'dislike'.")
        return value