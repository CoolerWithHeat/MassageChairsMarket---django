from django.shortcuts import render
from django.db.models import Count
from algoliasearch_django import raw_search
from rest_framework import generics
from .models import MassageChair
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import MassageChair, ChairReview, ReviewResponse, UserReaction
from .serializers import MassageChairSerializer, ChairReviewSerializer, ReviewResponseSerializer, UserReactionSerializer
from rest_framework import status
from django.conf import settings
import json, requests

def get_customer_location(ip_address):
    access_key = "2c1e63d646caa44a0dce4e0db6be494b"
    url = f'http://api.ipstack.com/{ip_address}?access_key={access_key}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            region_code = data.get('region_code')
            city = data.get('city')
            return f"{region_code}, {city}"
        else:
            print(f"Error: Unable to fetch data (status code: {response.status_code})")
            return None
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def extract_product_data(algolia_data):

   extracted_data = {
       "title": algolia_data["title"],
       "price": algolia_data["price"],
       "description": algolia_data["description"],
       "brand": algolia_data["brand"],
       "available_colors": algolia_data["color_options"],
       "features": algolia_data["chair_features"],
       "purchased": algolia_data["purchased"],
       "rating": algolia_data["rating"],
       "posted": algolia_data["posted"],
   }
   return extracted_data

def HomePage(request):
    return render(request, 'homePage-design/home.html')

def SearchPage(request):
    return render(request, 'homePage-design/searchPage.html')

def Buy(request, product_id):
    return render(request, 'homePage-design/Buy.html')

def FAQ(request):
    return render(request, 'homePage-design/FAQ.html')

def Cart(request):
    return render(request, 'homePage-design/finalcart.html')

class CheckCart(APIView):
    def post(self, request, *args, **kwargs):
        products = json.loads(request.body) if request.body else []
        total_price = 0
        verified_cart = []
        try:
            product_ids = [product['product_id'] for product in products]
            verified_products = MassageChair.objects.filter(id__in=product_ids)
            for each in verified_products:
                desired_product_id = each.id
                desired_product = next((product for product in products if product['product_id'] == desired_product_id), None)
                product_object = {}
                if desired_product:
                    product_object['id'] = each.id
                    product_object['title'] = each.title    
                    product_object['quantity'] = desired_product['quantity']
                    product_object['price'] = each.price
                    total_price += (each.price * desired_product['quantity'])
                    images = each.available_colors.all()
                    if images:
                        image_url = images[0].image.url
                        color = str(images[0])
                        product_object['color'] = color
                        product_object['image'] = image_url
                    verified_cart.append(product_object)
        except:
            pass
        return Response({'cart': verified_cart, 'total_price': total_price, 'verified_products':len(verified_cart)}, status=200)

class ChairReviewCreateAPIView(APIView):
    def post(self, request, chair_id, format=None):
        customer_ip_adress = get_client_ip(request)
        poster_location = get_customer_location(customer_ip_adress if not (customer_ip_adress == "127.0.0.1") else "102.129.145.173")
        review_quantity = ChairReview.objects.count()
        request.data['poster_location'] = poster_location
        request.data['posted_for'] = chair_id
        serializer = ChairReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            processed_data = serializer.data
            processed_data['customers_reaction'] = {'likes':0, 'dislikes':0}
            return Response(processed_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductReviewsEndpoint(generics.RetrieveAPIView):
    serializer_class = ChairReviewSerializer

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        queryset = ChairReview.objects.filter(posted_for_id=product_id)
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        review_quantity = ChairReview.objects.count()
        for review_data in serializer.data:
            review_id = review_data['id']
            review_data['replies'] = self.get_responses_for_review(review_id)
            review_data['customers_reaction'] = self.get_reactions_for_review(review_id)
            review_data['is_the_first'] = False if review_quantity else True
        return Response(serializer.data)

    def get_responses_for_review(self, review_id):
        reviewReplies = ReviewResponse.objects.filter(responded_to_id=review_id)
        if reviewReplies:
            serialized_reply = ReviewResponseSerializer(reviewReplies, many=True)
            return serialized_reply.data
        return []
    
    def get_reactions_for_review(self, review_id):
        reactions = UserReaction.objects.filter(to_review=review_id).values('action').annotate(count=Count('action'))

        likes = 0
        dislikes = 0
        for reaction in reactions:
            if reaction['action'] == UserReaction.LIKE:
                likes = reaction['count']
            elif reaction['action'] == UserReaction.DISLIKE:
                dislikes = reaction['count']

        return {'likes': likes, 'dislikes': dislikes}

class UserReactionCreateView(generics.CreateAPIView):
    serializer_class = UserReactionSerializer
    def create(self, request, *args, **kwargs):
        user_identity = request.data.get('user_identity')
        action = request.data.get('action')
        review_id = kwargs.get('review_id')
        try:
            chair_review = ChairReview.objects.get(id=review_id)
        except ChairReview.DoesNotExist:
            return Response({"error": "ChairReview not found."}, status=status.HTTP_404_NOT_FOUND)
        existing_reaction = UserReaction.objects.filter(user_identity=user_identity, to_review=chair_review).first()
        
        if existing_reaction:
            previous_action = existing_reaction.action
            if previous_action == action:
                return Response({"needs_increment": None, "needs_decrement": None}, status=status.HTTP_200_OK)
            else:
                existing_reaction.action = action
                existing_reaction.save()

                if action == 'like':
                    return Response({"needs_increment": "like", "needs_decrement": "dislike"}, status=status.HTTP_200_OK)
                else:
                    return Response({"needs_increment": "dislike", "needs_decrement": "like"}, status=status.HTTP_200_OK)
        else:
            data = {'user_identity': user_identity, 'action': action, 'to_review': chair_review.id}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if action == 'like':
                return Response({"needs_increment": "like", "needs_decrement": None}, status=status.HTTP_201_CREATED)
            else:
                return Response({"needs_increment": "dislike", "needs_decrement": None}, status=status.HTTP_201_CREATED)


class MassageChairDetailView(APIView):
    def get(self, request, product_ID, *args, **kwargs):
        try:
            chair = MassageChair.objects.get(id=product_ID)
            serialized = MassageChairSerializer(chair, many=False)
            return Response(serialized.data)
        except MassageChair.DoesNotExist:
            return Response({'message': 'Chair with id {} does not exist'.format(product_ID)}, status=status.HTTP_404_NOT_FOUND)