from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q, Sum
from datetime import timedelta
from algoliasearch_django import raw_search
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser
from .models import MassageChair, FAQ, product_track, ChairReview, ReviewResponse, UserReaction, Brand, SubscribedCustomers, discount_code, Payment_Session, ShippingInformation, product_track, CompanyContactInformation, CustomerInquiry
from .serializers import *
from django.conf import settings
from rest_framework.decorators import api_view
import json, stripe, random, string
from django.contrib.gis.geoip2 import GeoIP2
from django.utils.timezone import now
from .permissions import HasToBeAdmin

def generate_unique_id(): return random.randint(100000000000, 999999999999)

def GetCompanyContactInformation():
    company_details = CompanyContactInformation.objects.all()
    if company_details:
        serialized_details = CompanyContactInformationSerializer(company_details[0], many=False)
        return serialized_details.data
    return {}

def generate_order_number():
    current_year = 2024
    prefix = f"MC{current_year}"
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}{random_part}"

def get_customer_location(ip_address):
    g = GeoIP2()
    try:
        location = g.city(ip_address)
    except Exception as e:
        return None

    return location.get('region', None)
    
def GetDiscount(eligible='new_customer_only'):
    discounts = discount_code.objects.filter(eligible=eligible)
    if discounts:
        discount = max(discounts, key=lambda x: x.discount_amount)
        discount = DiscountCodeSerializer(discount, many=False)
        return discount.data
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
    filters = {
        "filters": "brand: Osaki",
    }
    response = raw_search(MassageChair, filters)

    print(response)
    return render(request, 'homePage-design/home.html')

def SearchPage(request):
    return render(request, 'homePage-design/searchPage.html')

def Buy(request, product_id):
    return render(request, 'homePage-design/Buy.html')

def FAQ(request):
    return render(request, 'homePage-design/FAQ.html')

def Cart(request):
    return render(request, 'homePage-design/finalcart.html')

def validate_color_for_chair(cart_data, chair_instance):
    selected_color = cart_data.get('selectedColor')
    available_colors = [color.color_name for color in chair_instance.available_colors.all()]
    if selected_color not in available_colors:
        return False
    else:
        return True
    
def CalculateWithDiscount(total=None, discount=None, multiplication=1):
    if total and discount:
        total_price = float(total)
        discount_amount_in_dollars = (float(total) / 100) * float(discount.get('amount')) if discount.get('type') == 'percentage' else float(discount.get('amount')) * multiplication
        return total_price - discount_amount_in_dollars
    
def validateSignature(discountData): return discountData if discountData.get('discount_code', None) else {}

class CheckCart(APIView):
    def post(self, request, *args, **kwargs):
        customer_data = json.loads(request.body) if request.body else []
        total_price = 0
        verified_cart = []
        verified_client_data = []
        message_to_customer = None
        message_needed = False
        try:
            products = customer_data['cart']
            requested_discount = customer_data.get('discount_details')
            requested_discount_code = requested_discount.get('requested_code') if requested_discount else None
            customer_email = requested_discount.get('customer_email') if requested_discount else None
            discount_applied = 0
            truely_requested = bool(requested_discount_code) and bool(customer_email)
            message_needed = truely_requested
            discount_signature = {}
            good = False
            if truely_requested:
                try:
                    verified_customer = None
                    try:verified_customer = SubscribedCustomers.objects.get(email=customer_email)
                    except: 'Exception occured for getting customer'
                    verified_discount_code = discount_code.objects.get(discount_code=requested_discount_code) if requested_discount_code else None
                    if isinstance(verified_discount_code, discount_code):
                        first_time_customer = (not verified_customer.used_first_time_discount or verified_customer == None) if verified_customer else False
                        for_new_customers = verified_discount_code.eligible == 'new_customer_only'
                        if (for_new_customers and first_time_customer) or (not first_time_customer and not for_new_customers) or (first_time_customer and not for_new_customers):
                            if isinstance(verified_customer, SubscribedCustomers): discount_signature['email'] = verified_customer.email
                            discount_applied = {'type': verified_discount_code.discount_type, 'amount': verified_discount_code.discount_amount, 'code': verified_discount_code.discount_code}
                            discount_signature['discount_code'] = verified_discount_code.discount_amount
                            discount_signature['code'] = verified_discount_code.discount_code
                            good = True
                        if (not first_time_customer) and (for_new_customers):
                            message_needed = True
                            message_to_customer = 'Sorry, this discount code is exclusive to newly subscribed emails.'
                    else:
                        message_needed = True
                        message_to_customer = 'Sorry, invalid discount code entered.'
                except:
                    message_to_customer = 'Sorry, invalid code. Please try again.'
            else: message_needed = False
            product_ids = [product['product_id'] for product in products]
            verified_products = MassageChair.objects.filter(id__in=product_ids)
            for verified_product in verified_products:
                desired_products = [product for product in products if product.get('product_id') == verified_product.id and product.get('selectedColor') == verified_product.get_exact_color(product['selectedColor']).color_name]
                verified_client_data = [*verified_client_data, *desired_products]
                for desired_product_data in desired_products:
                    available_color = validate_color_for_chair(desired_product_data, verified_product)
                    product_object = {}
                    if available_color:
                        product_object['id'] = verified_product.id
                        product_object['title'] = verified_product.title
                        product_object['quantity'] = desired_product_data['quantity']
                        product_object['price'] = verified_product.price
                        total_price += (verified_product.price * desired_product_data['quantity'])
                        requested_color = desired_product_data.get('selectedColor')
                        color_data = verified_product.get_exact_color(requested_color)
                        if color_data:
                            image_url = color_data.image.url
                            product_object['color'] = color_data.color_name
                            product_object['image'] = image_url
                            
                        verified_cart.append(product_object)          
        except Exception: Response(status=status.HTTP_501_NOT_IMPLEMENTED)
        
        return Response({'discount_signature': validateSignature(discount_signature) or None, 'cart': verified_cart, 'discount_applied': discount_applied or None, 'total_price': total_price, 'after_discount':CalculateWithDiscount(total_price, discount_applied) if discount_applied else None, 'verified_products': len(verified_cart), 'message_to_customer': message_to_customer if message_needed else None, 'update_data': verified_client_data}, status=200)

def UpdateProductReviewStatus(product_id):
    try:
        if product_id: 
            product = MassageChair.objects.get(id=product_id)
            if not product.has_reviewers:
                product.has_reviewers = True
                product.save()
    except: pass

def ValidateReview(data):
    for_product = MassageChair.objects.get(id=data.get('posted_for'))
    rate = data.get('customer_rate')
    poster = data.get('poster')
    if (not isinstance(for_product, MassageChair)) or (not rate) or (not poster): return None
    data['posted_for'] = for_product
    return data

def SaveReview(data):
    review = ChairReview.objects.create(**data)
    serializedReview = ChairReviewSerializer(review)
    return serializedReview.data

class ChairReviewCreateAPIView(APIView):
    def post(self, request, chair_id):
        customer_ip_adress = get_client_ip(request)
        poster_location = None
        try:
            poster_location = get_customer_location(customer_ip_adress)
            request.data['poster_location'] = poster_location
        except: pass
        request.data['posted_for'] = chair_id
        validData = ValidateReview(request.data)
        if validData:
            review = SaveReview(validData)
            review['customers_reaction'] = {'likes':0, 'dislikes':0}
            return Response(review, status=status.HTTP_201_CREATED)
        # serializer = ChairReviewSerializer(data=request.data)
        # print(request.data)
        # if serializer.is_valid():
        #     serializer.save()
        #     UpdateProductReviewStatus(chair_id)
        #     processed_data = serializer.data
        #     processed_data['customers_reaction'] = {'likes':0, 'dislikes':0}
        #     return Response(processed_data, status=status.HTTP_201_CREATED)
        # else: print(serializer.errors)
        return Response(status=status.HTTP_400_BAD_REQUEST)

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
    
class SaveCustomerQuestion(APIView): 
    def post(self, request):
        customer_data = json.loads(request.body) if request.body else None
        if customer_data:
            inquirySaved = CustomerInquiry.objects.create(**customer_data)
        return Response(status.HTTP_201_CREATED)

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

class FetchHomePage(APIView):
    def get(self, request, *args, **kwargs):
        brands = []
        brand_names = []
        for each_brand in Brand.objects.all():
            brand_names.append(each_brand.brand_name)
            if each_brand.brand_logo: brands.append(each_brand.brand_logo.url)

        filtered_objects = MassageChair.objects.filter(price__gte=5000)
        product_amount = len(filtered_objects)
        if not (product_amount >= 6) :
            filtered_objects = MassageChair.objects.filter(Q(purchased__gte=10) | Q(rating__gt=4.0))
        
        if (product_amount):
            serializedProducts = MassageChairSerializer(filtered_objects, many=True)
            new_customer_discount = GetDiscount()
            public_discount = GetDiscount('everyone')
            contactInformation = GetCompanyContactInformation()
            return Response({'products': serializedProducts.data, 'partners': brands, 'brand_names': brand_names, 'company_contact': contactInformation, 'available_discounts':{'new_customers_discount': new_customer_discount, 'public_discount':public_discount}}) 
        else:
            return Response({'message': 'no data available yet !'}, status=404)

def get_cart_details(products, discount=None):
    line_items = []
    verified_client_cart = []
    products_amount = len(products)
    each_reduction_as_discount = discount / products_amount if discount else 0
    verified_ids = []
    for item in products:
        product_id = item['product_id']
        quantity = item['quantity']
        color = item['selectedColor']
        product = get_object_or_404(MassageChair, id=product_id)
        exact_color = product.get_exact_color(color, True)
        line_items.append({
            'price_data': {
                'currency': 'usd',
                'unit_amount': int((float(product.price)-float(each_reduction_as_discount)) * 100),
                'product_data': {
                    'name': product.title,
                    'images': [exact_color.image.url if exact_color.image else None if exact_color else None],
                },
            },
            'quantity': quantity,
        })
        if (product and exact_color):
            verified_ids.append(product.id)
            verified_client_cart.append(item)
    return line_items, verified_ids, verified_client_cart

def GetCheckoutWithDiscount(discountData):
    try:
        if discountData:
            for_customer = discountData.get('email')
            code = discountData.get('code')
            if code:
                requested_code = None
                for_new_customers = True
                try:
                    requested_code = discount_code.objects.get(discount_code=code)
                    for_new_customers = requested_code.eligible == 'new_customer_only'
                except:
                    print('exception occured') 
                    pass
                good = False
                if for_new_customers:
                    try:
                        customer = SubscribedCustomers.objects.get(email=for_customer)
                        truely_first_time_customer = not customer.used_first_time_discount
                        if truely_first_time_customer: good = True
                    except: pass
                if not for_new_customers: 
                    if isinstance(requested_code, discount_code): good = True
            if good: return {'amount': requested_code.discount_amount, 'type': requested_code.discount_type, 'associated_email':for_customer}, requested_code 
        return {'amount': 0, 'type': 'fixed', 'associated_email':for_customer}, {}
    except:
        return None, None

def GetRawTotal(data):
    total = 0
    if len(data):
        for eachProductData in data:
            product_id = eachProductData.get('product_id')
            try:
                product = MassageChair.objects.get(id=product_id)
                total += product.price
            except:
                pass
    return total

def ValidateShipmentInformation(data):
    required_fields = ['firstname', 'address', 'country', 'zipcode', 'city', 'state', 'phone_number']
    for field in required_fields:
        if field not in data or not data[field]: return False
    if data['country'] != 'United States': return False
    return data

def check_session_payment(session_id):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.payment_status
        
        if payment_status == 'paid':
            return True
        else:
            return False
        
    except stripe.error.InvalidRequestError as e:
        print(f"Error: {e}")
        return False

def getExpectedPayment(total, discount):
    if total and isinstance(discount, dict):
        discount_type = discount.get('type')
        discount_amount = discount.get('amount')
        return (float(total) - float(discount_amount)) if discount_type == 'fixed' else (float(total) - float((total/100) * discount_amount))
    else:
        return total
    
def PrepareJsonDiscount(discount):
    if isinstance(discount, discount_code):
        discount = DiscountCodeSerializer(discount)
        return discount.data
    else: return None

@api_view(['POST'])
def InitiateCheckoutSession(request):
    # try:
    cart = request.data.get('cartProducts')
    discount_request = request.data.get('discountVerfication')
    shipping_details = request.data.get('shipping_information')
    print(discount_request)
    print('discount request was ', discount_request)
    discount_data = GetCheckoutWithDiscount(discount_request)
    print('last interpretation 1')
    print(discount_data)
    discount_amount_for_deduction = discount_data[0] if discount_data else None
    discount_instance = discount_data[1]
    print(discount_amount_for_deduction)
    print('last interpretation 2')
    print(discount_request)
    RawTotal = float(GetRawTotal(cart))
    print('last interpretation 3')
    processed_discount_details = discount_amount_for_deduction
    validShipmentData = ValidateShipmentInformation(shipping_details)
    print('last interpretation 4')
    print('after discount resulted in amount -->', getExpectedPayment(RawTotal, discount_amount_for_deduction))
    expected_payment = getExpectedPayment(RawTotal, discount_amount_for_deduction)
    print('last interpretation 5')
    if validShipmentData and len(cart) and RawTotal:
        if discount_amount_for_deduction: processed_discount_details = ((RawTotal / 100) * discount_amount_for_deduction.get('amount')) if discount_amount_for_deduction.get('type') == 'percentage' else discount_amount_for_deduction.get('amount')
        print('last interpretation 6')
        processed_data = get_cart_details(cart, processed_discount_details)
        cart_details = processed_data[0]
        verified_client_cart = processed_data[2]
        print('last interpretation 7')
        stripe.api_key = settings.STRIPE_SECRET_KEY
        print('last interpretation 8')
        if len(cart_details) > 0:
            new_order_number = generate_order_number()
            current_url = 'http://192.168.0.105/' if settings.DEBUG else 'https://massagechairsmarket/'
            checkout_session = stripe.checkout.Session.create(
                line_items=cart_details,
                mode='payment',
                success_url=current_url + f'Order/{new_order_number}/',
                cancel_url=current_url + f'order/fail/',
            )
            print('last interpretation 9')
            stripe_session = checkout_session.id
            shipping = ShippingInformation.objects.create(**validShipmentData)
            print('last interpretation 10')
            Payment_Session.objects.create(order_number=new_order_number, session=stripe_session, shipping_address=shipping, verified_cart=verified_client_cart, expected_amount=expected_payment, discount_code_used=PrepareJsonDiscount(discount_instance), associated_email = discount_amount_for_deduction.get('associated_email') if discount_amount_for_deduction else None)
            print('last interpretation 11')
            return Response({'sessionId': stripe_session})
    # except Exception as e:
    #     return Response({'error': str(e)}, status=400)

@api_view(['POST']) 
def customer_orders(request):
    try:
        sessions = json.loads(request.body) if request.body else [] 
        verified_orders = []
        orders_found = False
        if len(sessions):
            for each_session in sessions:
                try:
                    customer_payment = Payment_Session.objects.get(session=each_session)
                    if customer_payment.completed:
                        if not orders_found: orders_found = True
                        order = PaymentSessionSerializer(customer_payment)
                        verified_orders.append(order.data)
                    else:
                        pass
                except:
                    pass
        return Response({'verified_orders':verified_orders, 'orders_found': orders_found}, status=200)
    except:
        return Response({'verified_orders':[], 'orders_found': False}, status=200)

@api_view(['POST'])
def order_check(request, order_number):
    if (order_number) and (len(str(order_number)) == 12):
        try:
            order = Payment_Session.objects.get(order_number=order_number)
            if order:
                requested_order = PaymentSessionSerializer(order)
                return Response({'order': requested_order.data, 'orders_found':True})
            return Response({'order': None, 'orders_found':False})
        except:
            return Response({'order': None, 'orders_found':False})
    return Response({'order': None, 'orders_found':False})

def Payed(session):
    if not stripe.api_key: stripe.api_key = settings.STRIPE_SECRET_KEY
    payment = stripe.checkout.Session.retrieve(session)
    customer_paid = payment.payment_status == 'paid'
    try: return payment.amount_total / 100.0 if customer_paid else False
    except: return False

def get_tracking_info(session, product):
    tracking_available = product.brand.order_tracking_available
    product_id = product.id
    if tracking_available:
        try:
            tracking = product_track.objects.get(of_order=session, tracking_product=product)
            return {'tracking_status': tracking.tracking_stage, "tracking_available": tracking_available}
        except:
            tracking = product_track.objects.create(of_order=session, tracking_product=product)
            return {'tracking_status': tracking.tracking_stage, "tracking_available": tracking_available}
    else: 
        try:
            possible_tracking_detail = product_track.objects.get(of_order=session, tracking_product=product)
            possible_tracking_detail.delete()
            return None
        except: return None

def getExactColorProducts(verifiedCart=[], payment_session=None):
    found_products = []
    total = 0
    if isinstance(verifiedCart, list) and isinstance(payment_session, Payment_Session):
        for each_products in verifiedCart:
            product_id = each_products.get('product_id')
            product_color = each_products.get('selectedColor')
            product_quantity = each_products.get('quantity')
            retrieved_product = None
            try: retrieved_product = MassageChair.objects.get(id=product_id)
            except: pass
            if isinstance(retrieved_product, MassageChair) and product_color:
                product_tracking = get_tracking_info(payment_session, retrieved_product) or {}
                color_data = retrieved_product.get_exact_color(product_color)
                product_color = {'colorname':str(color_data), 'product_image': color_data.image.url if color_data.image else None}
                product_name = retrieved_product.title
                product_price = retrieved_product.price
                prepared_data = {'product_color': product_color, 'product_price':product_price, 'product_name': product_name, 'product_quantity': product_quantity, **product_tracking}
                found_products.append(prepared_data)
                total += (product_price * int(product_quantity))
    return found_products, total

def GetDiscountData(discount_used):return bool(discount_used)
    

@api_view(['GET']) 
def order_details(request, order_number):
    if (order_number) and (len(order_number) == 12):
        try:
            order = Payment_Session.objects.get(order_number=order_number)
            amount_paid = Payed(order.session)
            first_time_seeing = False
            updated_data = False
            was_for_new_customers = order.discount_code_used.get('eligible') == 'new_customer_only' if order else None
            customer = None
            try: customer = SubscribedCustomers.objects.get(email=order.associated_email) if order.associated_email else None
            except: pass
            if amount_paid:
                if order.first_time_view:
                    order.first_time_view = False
                    first_time_seeing = True
                    updated_data = True
                if was_for_new_customers and isinstance(customer, SubscribedCustomers):
                    if not customer.used_first_time_discount:
                        customer.used_first_time_discount = True
                        customer.save()
                if not order.completed: order.completed = True
                if updated_data: order.save()

                order_details = PaymentSessionSerializer(order)
                processed_order_details = order_details.data
                neccessary_amount = processed_order_details.get('expected_amount')
                payment_as_expected = amount_paid >= neccessary_amount - 3
                if payment_as_expected:
                    shipping_address = order_details.data.get('shipping_address')
                    ordered_products = processed_order_details.get('verified_cart')
                    discount_was_used = GetDiscountData(order.discount_code_used)
                    product_operation = getExactColorProducts(ordered_products, order) if ordered_products else None
                    the_right_products = product_operation[0]
                    subtotal = product_operation[1]
                    return Response({'order': processed_order_details, 'subtotal': subtotal, 'amount_paid': amount_paid, 'ordered_products': the_right_products, 'discount_used': order.discount_code_used if discount_was_used else None, 'first_time_seeing': first_time_seeing, 'shipping_details':shipping_address})
                else: 
                    order.delete()
                    return Response(status=404)
            else: 
                order.delete()
                return Response(status=404)
        except: return Response(status=404)
    else: return Response(status=404)

def initiatePayment(request): return render(request, "homePage-design/trial.html")

@api_view(['POST'])
def RegisterCustomer(request):
    email = request.data.get('email', None)
    name = request.data.get('name', None)
    is_new_customer = False
    if not email: return Response({'error': 'Email address is required'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        customer = SubscribedCustomers.objects.get(email=email)
        if not customer.used_first_time_discount:
            any_discount = discount_code.first_timer_discount()
            any_discount = DiscountCodeSerializer(any_discount, many=False)
            readied_discount = any_discount.data
            return Response({'discount': readied_discount, 'first_time_around':False, 'registered_email':email})
        return Response(status=409)
    except SubscribedCustomers.DoesNotExist:
        is_new_customer = True
        newCustomer = SubscribedCustomers.objects.create(email=email, name=name)
        if newCustomer:
            any_discount = discount_code.first_timer_discount()
            discountCode = DiscountCodeSerializer(any_discount)
            return Response({'discount': discountCode.data, 'first_time_around':is_new_customer, 'registered_email':email})
        else:
            Response({'discount': None}, status=500)

    return Response({'error': 'No discount codes found for this customer'}, status=status.HTTP_404_NOT_FOUND)

###################### ADMIN INTERFACE ENDPOINTS  ######################

from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models.functions import ExtractMonth, TruncMonth

def GetMonthlySalesCount(payments, current_year):
        monthly_amounts = payments.filter(
            created__year=current_year
        ).annotate(
            month_index=ExtractMonth('created')
        ).values('month_index').annotate(
            total_amount=Sum('expected_amount')
        ).order_by('month_index')
        monthly_sales = (
            payments
            .annotate(month=TruncMonth('created'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        monthly_sales_data = [0] * 12
        for entry in monthly_sales:
            month_index = entry['month'].month - 1
            monthly_sales_data[month_index] = entry['count']

        amounts_by_month = [0] * 12
        yearly_total = 0
        for month_data in monthly_amounts:
            month_index = month_data['month_index'] - 1
            amounts_by_month[month_index] = month_data['total_amount']
            yearly_total += month_data['total_amount']
        return {'each_month': amounts_by_month, 'total': yearly_total}, monthly_sales_data

def getOrdersPercentage(payments, today, yesterday):
    if len(payments):
        todays_sales = payments.filter(created__date=today)
        yesterdays_sales = payments.filter(created__date=yesterday)
        today_total_sales = len(todays_sales)
        yesterday_total_sales = len(yesterdays_sales)

        if yesterday_total_sales != 0:
            income_change_percent = ((today_total_sales - yesterday_total_sales) / yesterday_total_sales) * 100
        else:
            if today_total_sales > 0: income_change_percent = 100 * today_total_sales
            else: income_change_percent = 0
        return income_change_percent
    else:
        return None


class CompletedPaymentSessionsView(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        completed_sessions = Payment_Session.objects.filter(completed=True)
        today = now().date()
        yesterday = today - timedelta(days=1)
        subscribers = SubscribedCustomers.objects.count()
        todays_sessions = completed_sessions.filter(created__date=today)
        total_sum = completed_sessions.aggregate(total_sum=Sum('expected_amount'))['total_sum'] or 0
        todays_sum = todays_sessions.aggregate(todays_sum=Sum('expected_amount'))['todays_sum'] or 0

        yesterdays_sessions = completed_sessions.filter(created__date=yesterday)
        yesterdays_sum = yesterdays_sessions.aggregate(yesterdays_sum=Sum('expected_amount'))['yesterdays_sum'] or 0

        if yesterdays_sum != 0:
            income_change_percent = ((todays_sum - yesterdays_sum) / yesterdays_sum) * 100
        else:
            if todays_sum > 0 and not yesterdays_sum:
                income_change_percent = 100
            else:
                income_change_percent = 0
        completed_sessions_data = PaymentSessionSerializer(completed_sessions, many=True).data
        todays_sessions_data = PaymentSessionSerializer(todays_sessions, many=True).data
        current_year = today.year
        analytics = GetMonthlySalesCount(completed_sessions, current_year)
        monthly_income_analysis = analytics[0]
        monthly_sales_analysis = analytics[1]
        sales_increase_percentage = getOrdersPercentage(completed_sessions, today, yesterday)
        print(sales_increase_percentage)
        response_data = {
            'total_sales': completed_sessions_data,
            'todays_sales': todays_sessions_data,
            'total_income': total_sum,
            'todays_income': todays_sum,
            'income_change_percent': income_change_percent,
            'sales_change_percentage': sales_increase_percentage,
            'total_subscribers': subscribers,
            'monthly_income_analysis': monthly_income_analysis,
            'monthly_sales_analysis': monthly_sales_analysis,
        }
        return Response(response_data, status=status.HTTP_200_OK)

def Return_Base64_AsFile(base64_str, format='webp'):
    try:
        if isinstance(base64_str, str) and len(str(base64_str)):
            import base64
            from PIL import Image
            from io import BytesIO
            from django.core.files.base import ContentFile
            file_data = base64.b64decode(base64_str)
            file_obj = BytesIO(file_data)
            image = Image.open(file_obj)
            output = BytesIO()
            image.save(output, format=format)
            image_id = generate_unique_id()
            output.name = f'MC-{image_id}-COM.{format}'
            output.seek(0)
            content_file = ContentFile(output.getvalue(), name=output.name)
            return content_file
    except: None

def getColors(data=[]):
    if isinstance(data, list):
        colors = []
        for each_color_date in data:
            each_color_date['image'] = Return_Base64_AsFile(each_color_date.get('image'))
            productColor = Color_Options.objects.create(**each_color_date)
            colors.append(productColor.id)
        return colors
    return []

def getAdditionalImages(data=[]):
    if isinstance(data, list):
        colors = []
        for each_color_date in data:
            each_color_date['image'] = Return_Base64_AsFile(each_color_date.get('image'))
            productColor = Additional_Images.objects.create(**each_color_date)
            colors.append(productColor.id)
        return colors
    return []

def getFeatures(data=[]):
    if isinstance(data, list):
        colors = []
        from .models import showcase_side_options
        for each_color_date in data:
            requested_side = each_color_date.get('feature_side')
            each_color_date['feature_showcase'] = Return_Base64_AsFile(each_color_date.get('feature_showcase'))
            try:
                showcase_side = showcase_side_options[each_color_date.get('feature_side') - 1][0] if requested_side else None
                each_color_date['feature_side'] = showcase_side
            except: pass
            productColor = ChairFeature.objects.create(**each_color_date)
            colors.append(productColor.id)
        return colors
    return []

def getVideos(data=[]):
    if isinstance(data, list):
        colors = []
        from .models import showcase_side_options, videoPlatforms
        for each_color_date in data:
            showcase_side = int(each_color_date.get('video_side')) or 0
            showcase_platform = int(each_color_date.get('video_platform')) or 0
            each_color_date['video_side'] = showcase_side_options[showcase_side-1][0] if showcase_platform else 'any side'
            each_color_date['video_platform'] = videoPlatforms[showcase_platform-1][0] if showcase_platform else 'youtube'
            productColor = VideoShowcase.objects.create(**each_color_date)
            colors.append(productColor.id)
        return colors
    return []

def AddColorOptions(product, color_ids=[]):
    if product and isinstance(color_ids, list):
        for each_color_id in color_ids:
            color = Color_Options.objects.get(id=each_color_id)
            product.available_colors.add(color)

def AddAdditionalImages(product, color_ids=[]):
    if product and isinstance(color_ids, list):
        for each_color_id in color_ids:
            color = Additional_Images.objects.get(id=each_color_id)
            product.additional_images.add(color)

def AddFeatures(product, color_ids=[]):
    if product and isinstance(color_ids, list):
        for each_color_id in color_ids:
            color = ChairFeature.objects.get(id=each_color_id)
            product.features.add(color)

def AddVideoDemos(product, color_ids=[]):
    if product and isinstance(color_ids, list):
        for each_color_id in color_ids:
            color = VideoShowcase.objects.get(id=each_color_id)
            product.video_demo.add(color)

def images_are_different(image1_binary, image2_binary):return image1_binary != image2_binary

class SaveProduct(APIView):
    permission_classes = [HasToBeAdmin]
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        incoming_data = json.loads(request.body) or None
        requested_brand = incoming_data.get('brand')
        available_colors = incoming_data.get('available_colors')
        additional_images = incoming_data.get('additional_images')
        product_features = incoming_data.get('features')
        product_videos = incoming_data.get('video_demo')
        # reference variables !!!!
        product_colors = []
        product_additional_images = []
        features = []
        video_demos = []
        print(len(available_colors or []))
        print(len(additional_images or []))
        if (incoming_data):
            of_brand = Brand.objects.get(brand_name=requested_brand)
            incoming_data['brand'] = of_brand
            if available_colors: product_colors = getColors(incoming_data.pop('available_colors'))
            if additional_images: product_additional_images = getAdditionalImages(incoming_data.pop('additional_images'))
            if product_features: features = getFeatures(incoming_data.pop('features'))
            if product_videos: video_demos = getVideos(incoming_data.pop('video_demo'))
            created_product = MassageChair.objects.create(**incoming_data)
            AddColorOptions(created_product, product_colors)
            AddAdditionalImages(created_product, product_additional_images)
            AddFeatures(created_product, features)
            AddVideoDemos(created_product, video_demos)
            created_product.save()
            serialized_product = MassageChairSerializer(created_product, many=False)
            return Response(serialized_product.data, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_201_CREATED)

class GetProducts(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        products = MassageChair.objects.all()
        brands = Brand.objects.all()
        serializedProducts = MassageChairSerializer(products, many=True)
        serializedBrands = BrandSerializer(brands, many=(len(brands) > 1))
        return Response({'products': serializedProducts.data, 'brands':serializedBrands.data}, status=status.HTTP_201_CREATED)

def HandleFeatureUpdate(model, data, operation_type):
    if operation_type == 'add':
        data['feature_showcase'] = Return_Base64_AsFile(data.get('feature_showcase'))
        print(data.get('feature_side'))
        # if (data.get('feature_side')): data['feature_side'] = showcase_side_options[int(data.pop('feature_side'))-1][0]
        feature = ChairFeature.objects.create(**data)
        model.features.add(feature)
        serialized_feature = ChairFeatureSerializer(feature, many=False)
        return serialized_feature.data
    if operation_type == 'remove':
        requested_id = data.get('feature_id')
        if requested_id:
            feature = ChairFeature.objects.get(id=requested_id)
            serialized_feature = ChairFeatureSerializer(feature, many=False)
            feature.delete()
            final_data = serialized_feature.data
            final_data['id'] = requested_id
            return final_data
    return {}

def HandleChairColor(model, data, operation_type):
    if operation_type == 'add':
        data['image'] = Return_Base64_AsFile(data.get('image'))
        color = Color_Options.objects.create(**data)
        model.available_colors.add(color)
        serialized_color = ColorOptionsSerializer(color, many=False)
        return serialized_color.data
    if operation_type == 'remove':
        requested_id = data.get('color_id')
        if requested_id:
            chair_color = Color_Options.objects.get(id=requested_id)
            serialized_color = ColorOptionsSerializer(chair_color, many=False)
            chair_color.delete()
            final_data = serialized_color.data
            final_data['id'] = requested_id
            return final_data
    return {}

def HandleAdditionalImages(model, data, operation_type):
    if operation_type == 'add':
        data['image'] = Return_Base64_AsFile(data.get('image'))
        product_image = Additional_Images.objects.create(**data)
        model.additional_images.add(product_image)
        serialized_image = {'id':product_image.id, 'image':product_image.image.url}
        return serialized_image
    if operation_type == 'remove':
        requested_id = data.get('image_id')
        if requested_id:
            chair_image = Additional_Images.objects.get(id=requested_id)
            serialized_color = {'id':chair_image.id, 'image':chair_image.image.url}
            chair_image.delete()
            return serialized_color
    return {}

def HandleVideoDemo(model, data, operation_type):
    if operation_type == 'add':
        if (data.get('video_platform')): data['video_platform'] = videoPlatforms[int(data.pop('video_platform'))-1][0]
        if (data.get('video_side')): data['video_side'] = showcase_side_options[int(data.pop('video_side'))-1][0]
        product_video = VideoShowcase.objects.create(**data)
        model.video_demo.add(product_video)
        serialized_video = {'id': product_video.id, 'showcase_text':product_video.showcase_text, 'video_side':product_video.video_side, 'video_platform':product_video.video_platform, 'video_id':product_video.video_id}
        return serialized_video
    if operation_type == 'remove':
        requested_id = data.get('video_id')
        if requested_id:
            video = VideoShowcase.objects.get(id=requested_id)
            serialized_video = {'id': video.id, 'showcase_text':video.showcase_text, 'video_side':video.video_side, 'video_platform':video.video_platform, 'video_platform':video.video_id}
            video.delete()  
            return serialized_video
    return {}

def UpdateProductTextInformation(model, data, operation_type):
    if operation_type == 'add':
        requested_brand = Brand.objects.get(brand_name=data.pop('brand'))
        for key, value in data.items():
            setattr(model, key, value)
        if isinstance(requested_brand, Brand): model.brand = requested_brand
        model.save()
        serialized_product = MassageChairSerializer(model, many=False)
        return serialized_product.data
    return {}

class UpdateProduct(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, product_id):
        requested_product = MassageChair.objects.get(id=product_id)
        data = json.loads(request.body) or {}
        operation_indecies = {
            'all_text': UpdateProductTextInformation,
            'features': HandleFeatureUpdate,
            'available_colors': HandleChairColor,
            'additional_images':HandleAdditionalImages,
            'video_demo':HandleVideoDemo,
        }
        if requested_product and data:
            if data.get('operation') == 'delete':
                print('delete requested !!!')
                product_details = MassageChairSerializer(requested_product, many=False).data
                requested_product.delete()
                return Response(product_details, status=status.HTTP_200_OK)
            operation_point = data.get('to_model')
            operation_type = data.get('do')
            data_for_operation = data.get('data')
            request_operator = operation_indecies.get(operation_point)
            if operation_point and operation_point and callable(request_operator):
                added_object = request_operator(requested_product, data_for_operation, operation_type)
                return Response(added_object, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_201_CREATED)

class GetBrands(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        brands = Brand.objects.all()
        serializedBrands = BrandSerializer(brands, many=True)
        return Response(serializedBrands.data, status=status.HTTP_200_OK)

class UpdateBrand(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, brand_id):
        requested_brand = Brand.objects.get(id=brand_id)
        data = json.loads(request.body) or {}
        if isinstance(requested_brand, Brand) and data:
            if data.get('operation') == 'delete':
                requested_brand.delete()
                return Response({}, status=status.HTTP_200_OK)
            for key, value in data.items():
                if key == 'brand_logo': setattr(requested_brand, key, Return_Base64_AsFile(value))
                else: setattr(requested_brand, key, value)
            requested_brand.save()
            serialized_brand = BrandSerializer(requested_brand, many=False)
            return Response(serialized_brand.data, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_201_CREATED)

class CreateBrand(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        data = json.loads(request.body) or {}
        if data:
            if data.get('brand_logo'):data['brand_logo'] = Return_Base64_AsFile(data.pop('brand_logo'))
            created_brand = Brand.objects.create(**data)
            serialized_brand = BrandSerializer(created_brand, many=False)
            return Response(serialized_brand.data, status=status.HTTP_201_CREATED)
        return Response({}, status=status.HTTP_201_CREATED)

class GetDiscounts(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        discounts = discount_code.objects.all()
        serializedDiscounts = DiscountCodeSerializer(discounts, many=True)
        print(serializedDiscounts.data)
        return Response(serializedDiscounts.data, status=status.HTTP_200_OK)

class CreateDiscount(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        data = json.loads(request.body) or {}
        if data:
            discount = discount_code.objects.create(**data)
            serializedDiscount = DiscountCodeSerializer(discount, many=False)
            return Response(serializedDiscount.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class UpdateDiscount(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, discount_id):
        requested_discount = discount_code.objects.get(id=discount_id)
        data = json.loads(request.body) or {}
        discount_hook = None
        if requested_discount and data:
            discount_hook = requested_discount
            if data.get('operation') == 'delete':
                requested_discount.delete()
                serializedDiscount = DiscountCodeSerializer(discount_hook, many=False)
                return Response(serializedDiscount.data, status=status.HTTP_200_OK)
            for key, value in data.items():
                setattr(requested_discount, key, value)
            requested_discount.save()
            serializedDiscount = DiscountCodeSerializer(discount_hook, many=False)
            return Response(serializedDiscount.data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

class GetOrders(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        orders = Payment_Session.objects.all()
        serializedOrders = PaymentSessionSerializer(orders, many=True)
        return Response(serializedOrders.data, status=status.HTTP_200_OK)

class UpdateShippingData(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, data_id):
        requested_shipping_data = ShippingInformation.objects.get(id=data_id)
        data = json.loads(request.body) or {}
        if data and requested_shipping_data:
            print(data)
            for key, value in data.items():
                setattr(requested_shipping_data, key, value)
            requested_shipping_data.save()
        return Response({}, status=status.HTTP_200_OK)

class UpdateOrder(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, data_id):
        requested_order = Payment_Session.objects.get(id=data_id)
        data = json.loads(request.body) or {}
        if data and isinstance(requested_order, Payment_Session):
            if data.get('operation') == 'delete':
                requested_order.delete()
                return Response({}, status=status.HTTP_200_OK)
            for key, value in data.items():
                setattr(requested_order, key, value)
            requested_order.save()
        return Response({}, status=status.HTTP_200_OK)

class UpdateContact(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        data = json.loads(request.body) or {}
        if isinstance(data, dict):
            company_contact = CompanyContactInformation.objects.all()[0]
            if (company_contact):
                for key, value in data.items():
                    setattr(company_contact, key, value)
                company_contact.save()
            return Response({}, status=status.HTTP_200_OK)

class GetCompanyContactData(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        company_contact = CompanyContactInformation.objects.all()[0]
        serializedContact = CompanyContactInformationSerializer(company_contact, many=False)
        return Response(serializedContact.data, status=status.HTTP_200_OK)

class GetOrderTracking(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        OrderTrackings = product_track.objects.all()
        serializedTracking = TrackingSerializer(OrderTrackings, many=True)
        return Response(serializedTracking.data, status=status.HTTP_200_OK)

class UpdateTrackingData(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        data = json.loads(request.body) or {}
        if isinstance(data, list):
            for each_tracking_data in data:
                trackingStages = ['Order Confirmed', 'Processing', 'On the way', 'Delivered']
                if isinstance(each_tracking_data, dict):
                    tracking_id = each_tracking_data.get('track_id')
                    requested_model_instance = product_track.objects.get(id=tracking_id)
                    purge_requested = each_tracking_data.get('operation') == 'delete'
                    if purge_requested:
                        requested_model_instance.delete()
                    else:
                        if isinstance(requested_model_instance, product_track):
                            for key, value in each_tracking_data.items():
                                if key == 'tracking_stage': value=trackingStages.index(value)+1
                                print(value)
                                setattr(requested_model_instance, key, value)
                            requested_model_instance.save()
        return Response({}, status=status.HTTP_200_OK)

def create_or_update_token(user):
    expiration_period = timedelta(days=7)
    expires_at = timezone.now() + expiration_period
    token, created = AdvancedToken.objects.get_or_create(user=user)
    token.expires_at = expires_at
    token.save()
    return token
    
class AuthenticateAdmin(APIView):
    def post(self, request):
        from .models import CustomUser
        data = json.loads(request.body) or {}
        email = data.get('email')
        password = data.get('password')
        if email and password:
            admin = None
            try: admin = CustomUser.objects.get(email=email)
            except: pass
            if isinstance(admin, CustomUser):
                validPassword = admin.check_password(password)
                if validPassword:
                    token = create_or_update_token(admin)
                    return Response({'token': str(token)}, status=status.HTTP_200_OK)
            return Response({}, status=status.HTTP_404_NOT_FOUND)
        return Response({}, status=status.HTTP_404_NOT_FOUND)
    
class AllReviews(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        reviews = ChairReview.objects.all()
        serializedReviews = AdminReviewsSerializer(reviews, many=True)
        return Response(serializedReviews.data, status=status.HTTP_200_OK)

class RemoveReview(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, review_id):
        review = ChairReview.objects.get(id=review_id)
        if review:
            review.delete()
        return Response({}, status=status.HTTP_200_OK)

class CheckIfAdmin(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        return Response({}, status=status.HTTP_202_ACCEPTED)


class GetCustomerInquiries(APIView):
    permission_classes = [HasToBeAdmin]
    def get(self, request):
        inquiries = CustomerInquiry.objects.all()
        serializedQuestions = CustomerInquirySerializer(inquiries, many=True)
        return Response(serializedQuestions.data, status=status.HTTP_200_OK)
    
class UpdateInquiryStatus(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        data = json.loads(request.body) or {}
        requested_id = data.get('id')
        requested_status = data.get('handled', False)
        if requested_id:
            requestedInquiry = get_object_or_404(CustomerInquiry, id=requested_id)
            if requestedInquiry:
                requestedInquiry.handled = requested_status
                requestedInquiry.save()
                return Response({}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
class GetFAQs(APIView):
    def get(self, request):
        from .models import FAQ
        FAQs = FAQ.objects.order_by('priority')
        serializedFAQs = FAQ_serializer(FAQs, many=True)
        return Response(serializedFAQs.data, status=status.HTTP_200_OK)

class UpdateFAQ(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, FAQ_id):
        from .models import FAQ
        requestedFAQ = get_object_or_404(FAQ, id=FAQ_id)
        if requestedFAQ:
            data = json.loads(request.body) or {}
            priorityClashPossible = get_object_or_404(FAQ, priority=data.get('priority'))
            if not (priorityClashPossible == requestedFAQ) and priorityClashPossible:
                return Response({'error': 'Priority clash'}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            
            for key, value in data.items():
                print('setting', key, 'as', value)
                setattr(requestedFAQ, key, value)
            print('saving')
            requestedFAQ.save()
            return Response({}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)
    
class CreateFAQ(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request):
        from .models import FAQ
        data = json.loads(request.body) or {}
        if data:
            new_FAQ = FAQ.objects.create(**data)
            new_FAQ.save()
            return Response({}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)

class SwapFAQs(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, FAQ_id):
        from .models import FAQ
        data = json.loads(request.body) or {}
        faq_being_replaced = data.get('priority')
        try:
            if faq_being_replaced and FAQ_id:
                faq_being_replaced = get_object_or_404(FAQ, priority=faq_being_replaced)
                new_replacement_id = FAQ.objects.count() + 1
                faq_being_replaced.priority = new_replacement_id
                faq_being_replaced.save()
                FAQ_being_saved = FAQ.objects.create(**data)    
                return Response({}, status=status.HTTP_200_OK)
        except: pass
        return Response(status=status.HTTP_404_NOT_FOUND)

class SwapEach(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, FAQ_id, FAQ_at_priority):
        from .models import FAQ
        # try:
        if FAQ_id and FAQ_at_priority:
            faq1 = get_object_or_404(FAQ, id=FAQ_id)
            faq2 = get_object_or_404(FAQ, priority=FAQ_at_priority)
            if faq1 and faq2:
                print(faq1)
                print(faq2)
                temp_priority1 = faq1.priority
                temp_priority2 = faq2.priority
                faq1.priority = 99999
                faq2.priority = temp_priority1

                faq1.save()
                faq2.save()
                faq1.priority = temp_priority2
                faq1.save()
            return Response({}, status=status.HTTP_200_OK)
        # except: pass
        return Response(status=status.HTTP_404_NOT_FOUND)

class RemoveFAQ(APIView):
    permission_classes = [HasToBeAdmin]
    def post(self, request, FAQ_id):
        from .models import FAQ
        faq_being_removed = get_object_or_404(FAQ, id=FAQ_id)
        if faq_being_removed:
            faq_being_removed.delete()
            return Response({}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)