from algoliasearch_django import AlgoliaIndex
import algoliasearch_django as algoliasearch
from .models import MassageChair

class ChairIndex(AlgoliaIndex):
    fields = ('id', 'title', 'brand', 'price', 'discount_amount', 'description', 'purchased', 'rating', 'posted', 'color_options', 'chair_features', 'FilterOptions', 'available_colors_found', 'additional_images_found', 'chair_features_found', 'video_demonstrations_found', 'has_reviewers')

    settings = {
        'searchableAttributes': ['title', 'brand', 'price', 'description', 'rating', 'posted', 'purchased', 'chair_features'],
        'attributesForFaceting': ['brand', 'chair_features']
    }

algoliasearch.register(MassageChair, ChairIndex)