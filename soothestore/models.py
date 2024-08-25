from django.db import models
from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from rest_framework.authtoken.models import Token
from django.dispatch import receiver

showcase_side_options = (
    ('any side', 'any side'),
    ('left', 'left'),
    ('right', 'right'),
)

videoPlatforms = (
    ('youtube', 'youtube'),
    ('vimeo', 'vimeo'),
)

discount_types = (
    ('fixed', 'fixed'),
    ('percentage', 'percentage'),
)

eligibility_types = (
    ('new_customer_only', 'new customer only'),
    ('everyone', 'everyone'),
)

ORDER_STATUS_STAGES = [
    (1, 'Order Confirmed'),
    (2, 'Processing'),
    (3, 'On the way'),
    (4, 'Delivered'),
]

def RetrieveDate(Raw_Date):
    day = Raw_Date.day
    month = Raw_Date.month
    year = Raw_Date.year
    return day, month, year

class ProductMeta(models.Model):
    meta_description = models.TextField(max_length=160, blank=True, null=True, help_text="Description for SEO, max 160 characters.")
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated SEO keywords.")
    # Open Graph fields
    og_title = models.CharField(max_length=255, blank=True, null=True, help_text="Title for Open Graph, defaults to product title if blank.")
    og_description = models.TextField(max_length=160, blank=True, null=True, help_text="Description for Open Graph, defaults to meta_description if blank.")
    og_image = models.URLField(help_text="URL of the image for Open Graph.", blank=True, null=True,)
    og_url = models.URLField(blank=True, null=True, help_text="Canonical URL of the product for Open Graph.")
    og_type = models.CharField(max_length=50, blank=True, null=True, default='product', help_text="Type of content, e.g., product, article, etc.")

    def __str__(self):
        return f"Meta for {self.meta_keywords}"

class ChairFeature(models.Model):
    called = models.CharField(max_length=120, default=None)
    feature_side = models.CharField(max_length=35, choices=showcase_side_options, default='any side')
    feature_description = models.TextField(max_length=655, default=None, blank=True, null=True)
    feature_showcase = models.ImageField(default=None, blank=True, null=True)
    def __str__(self): return str(self.called)

class CompanyContactInformation(models.Model):
    phone_number = models.CharField(max_length=25, default=None, blank=True)
    company_email = models.EmailField(max_length=255, default=None, blank=True)
    def __str__(self): return f'{self.phone_number} || {self.company_email}'

class SubscribedCustomers(models.Model):
    email = models.EmailField(max_length=60, blank=False, null=False, unique=True)
    name = models.CharField(max_length=120, default=None, blank=True, null=True)
    used_first_time_discount = models.BooleanField(default=False)
    customer_discount_codes = models.ManyToManyField('discount_code', related_name='customer_discount_code', blank=True)
    def __str__(self): return str(self.email)
    
class VideoShowcase(models.Model):
    showcase_text = models.TextField(max_length=580, default=None, blank=True, null=True)
    video_side = models.CharField(max_length=35, choices=showcase_side_options, default='any side')
    video_platform = models.CharField(max_length=35, choices=videoPlatforms, default='vimeo')
    video_id = models.CharField(max_length=60, default=None, blank=False, null=False)
    
    def __str__(self): return f"{self.video_platform} video"
        
    class Meta: verbose_name_plural = "Video Demonstrations"

class ChairType(models.Model):
    called = models.CharField(max_length=60)
    def __str__(self): return str(self.called)

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.CharField(max_length=620)
    priority = models.IntegerField(default=1, unique=True)
    def __str__(self): return str(self.question)

class Brand(models.Model):
    brand_name = models.CharField(max_length=20)
    brand_logo = models.ImageField(default=None, blank=True, null=True)
    authorized_in = models.DateTimeField(auto_now_add=True)
    order_tracking_available = models.BooleanField(default=False, blank=False, null=False)
    def __str__(self): return str(self.brand_name)

class product_track(models.Model):
    of_order = models.ForeignKey('Payment_Session', on_delete=models.CASCADE)
    tracking_product = models.ForeignKey('MassageChair', on_delete=models.CASCADE)
    order_number_provided_by_brand = models.CharField(max_length=35, default="No Tracking Code")
    tracking_stage = models.IntegerField(default=1, choices=ORDER_STATUS_STAGES, blank=False, null=False)

    class Meta: verbose_name_plural = "Orders Tracks"
    def __str__(self): return f"of ${int(self.of_order.expected_amount)} Order || {self.of_order.order_number}"

class Payment_Session(models.Model):
    order_number = models.CharField(max_length=12, default=None, unique=True, blank=False, null=False)
    associated_email = models.EmailField(default=None, blank=True, null=True)
    session = models.CharField(max_length=620, blank=False, null=False)
    expected_amount = models.FloatField(default=None, blank=False, null=False)
    completed = models.BooleanField(default=False)
    verified_cart = models.JSONField(default=dict, null=False, blank=False)
    shipping_address = models.OneToOneField('ShippingInformation', on_delete=models.CASCADE, default=None)
    discount_code_used = models.JSONField(default=dict, blank=True, null=True)
    first_time_view = models.BooleanField(default=True)
    order_closed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    def __str__(self): return "Completed Order" if self.completed else "Uncompleted Order"

class ShippingInformation(models.Model):
    firstname = models.CharField(max_length=255, default=None)
    lastname = models.CharField(max_length=255, blank=True, null=True, default=None)
    apartment_suite = models.CharField(max_length=255, blank=True, null=True, default=None)
    address = models.CharField(max_length=255, default=None)
    country = models.CharField(max_length=255, default='United States')
    zipcode = models.CharField(max_length=20, default=None)
    city = models.CharField(max_length=255, default=None)
    state = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    def __str__(self): return f'{self.firstname} {self.lastname} - {self.address}, {self.city}, {self.state}, {self.zipcode}, {self.country}'

class MassageChair(models.Model):
    title = models.CharField(max_length=60)
    brand = models.ForeignKey(Brand, on_delete=models.DO_NOTHING)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    description = models.TextField(default=None)
    available_colors = models.ManyToManyField('Color_Options', related_name='massage_chairs')
    additional_images = models.ManyToManyField('Additional_Images', related_name='additional_product_images', blank=True)
    video_demo = models.ManyToManyField(VideoShowcase, related_name='video_demonstration', blank=True)
    features = models.ManyToManyField(ChairFeature, related_name='Massage_Features', blank=True)
    product_meta = models.ForeignKey(ProductMeta, on_delete=models.SET_NULL, default=None, blank=True, null=True)
    purchased = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0, validators=[MaxValueValidator(limit_value=5.0)])
    posted = models.DateTimeField(default=timezone.now)
    has_reviewers = models.BooleanField(default=False)
   
    @property
    def available_colors_found(self):
        colors = self.available_colors.all()
        if len(colors):
            from .serializers import ColorOptionsSerializer
            try:
                many = len(colors) > 1
                serialized_colors = ColorOptionsSerializer(colors, many=many)
                return serialized_colors.data
            except: pass
        return []

    @property
    def additional_images_found(self):
        additiona_images = self.additional_images.all()
        if len(additiona_images):
            try:
                return [images.image.url for images in additiona_images if images.image]
            except: pass
        return []

    @property
    def meta_data(self):
        from .serializers import ProductMetaSerializer
        meta = self.product_meta or None
        if meta: meta = ProductMetaSerializer(meta).data
        return meta or {}
    
    @property
    def chair_features_found(self):
        features = self.features.all()
        if len(features):
            try:
                return [{'id': feature.id, 'called': feature.called, 'showcase_side': feature.feature_side, 'information': feature.feature_description, 'image':feature.feature_showcase.url} for feature in features]
            except: pass
        return []

    @property
    def video_demonstrations_found(self):
        demos = self.video_demo.all()
        if len(demos):
            try:
                return [{'id': demo.id, 'video_id':demo.video_id, 'video_side':demo.video_side, 'platform': demo.video_platform, 'information': demo.showcase_text} for demo in demos]
            except: pass
        return []
    
    def color_options(self):
        colors = self.available_colors.all()
        return [[str(color.color_name), str(color.color_code), str(color.image.url)] for color in colors]
    
    def get_exact_color(self, color_name, whole_object=True):
        try:
            color = self.available_colors.get(color_name__iexact=color_name)
            if not whole_object: return str(color.image.url) if color.image else None
            else: return color
        except: return None
    
    def chair_features(self):
        features = self.features.all()
        return [str(feature.called) for feature in features]
    
    @property
    def FilterOptions(self):
        brandFilters = []
        featureFilters = []
        for eachBrand in Brand.objects.all():
            brandName = eachBrand.brand_name
            brandCount = len(MassageChair.objects.filter(brand=eachBrand))
            finalData = {}
            finalData[brandName] = brandCount
            brandFilters.append(finalData)
        for eachFeature in ChairFeature.objects.all():
            featureName = eachFeature.called
            featureCount = len(MassageChair.objects.filter(features=eachFeature))
            finalData = {}
            finalData[featureName] = featureCount
            featureFilters.append(finalData)
        return {'Brands':brandFilters, 'Features':featureFilters}

    
    def posted(self): return 'today'

    def save(self, *args, **kwargs):
        self.brand_name = self.brand.brand_name
        super().save(*args, **kwargs)

    def __str__(self): return self.title

class CustomerInquiry(models.Model):
    customer_email = models.EmailField(max_length=255, default=None, blank=False)
    customer_name = models.CharField(max_length=60, default=None, blank=False)
    customer_question = models.TextField(default=None)
    asked_date = models.DateTimeField(default=timezone.now)
    handled = models.BooleanField(default=False)
    def __str__(self): return f'question by {self.customer_name}'

class ChairReview(models.Model):
    posted_for = models.ForeignKey(MassageChair, on_delete=models.CASCADE)
    poster = models.CharField(max_length=35, default='Anonymous')
    poster_location = models.CharField(max_length=35, default=None, blank=True, null=True)
    customer_rate = models.IntegerField(default=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
    )
    review_text = models.TextField(default=None, blank=True, null=True)
    posted_date = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'Review By {str(self.poster)}'

class ReviewResponse(models.Model):
    responded_to = models.ForeignKey(ChairReview, on_delete=models.CASCADE)
    poster = models.CharField(max_length=35, default='Massage Chairs')
    response_text = models.TextField(default='')
    responded_date = models.DateTimeField(default=timezone.now)
    def __str__(self): return f'Review Response by Business'

class Color_Options(models.Model):
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=50, blank=True, null=True)
    image = models.ImageField(default=None, blank=True, null=True)

    def __str__(self): return self.color_name
    class Meta: verbose_name_plural = "Chair Colors"

class Additional_Images(models.Model):
    image = models.ImageField(default=None, blank=True, null=True)
    def __str__(self):
        return 'Additional Image'
    
    class Meta:
        verbose_name_plural = "Chair Colors"

class UserReaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'

    PREFERENCE_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    to_review = models.ForeignKey(ChairReview, on_delete=models.CASCADE)
    user_identity = models.CharField(max_length=50)
    action = models.CharField(max_length=8, choices=PREFERENCE_CHOICES, default=LIKE)

    def __str__(self):
        return self.action

class discount_code(models.Model):
    discount_title = models.CharField(max_length=220, blank=True, null=True)
    discount_amount = models.IntegerField(default=200, blank=False, null=False)
    discount_type = models.CharField(max_length=10, default='fixed', choices=discount_types, blank=False, null=False)
    eligible = models.CharField(max_length=17, choices=eligibility_types, default='everyone')
    is_public = models.BooleanField(default=True)
    discount_code = models.CharField(max_length=8, default=None, blank=True, null=True)
    
    class Meta: verbose_name_plural = "Discounts"
    
    def __str__(self):
        is_fixed = self.discount_type == 'fixed'
        discount_sign = '$' if is_fixed else '%'
        discount_amount = discount_sign + str(self.discount_amount) if is_fixed else str(self.discount_amount) + discount_sign
        return f'{discount_amount} discount {"not" if not self.is_public else ""} on public'
    
    @classmethod
    def highest_amount_discount(cls):
        discounts = cls.objects.all()
        if not discounts:
            return None
        highest_discount = max(discounts, key=lambda x: x.discount_amount)
        return highest_discount
    
    @classmethod
    def first_timer_discount(cls):
        discounts = cls.objects.filter(eligible='new_customer_only')
        return None if not discounts else discounts[0]


@receiver([post_save, post_delete], sender=ChairReview)
def update_products_status(sender, instance, **kwargs):
    effected_product = instance.posted_for
    reviews_left = sender.objects.filter(posted_for=effected_product)
    effected_product.has_reviewers = True if len(reviews_left) else False
    effected_product.save()

@receiver([post_save, post_delete], sender=Brand)
def update_related_products(sender, instance, **kwargs):
    related_products = MassageChair.objects.filter(brand=instance)
    for product in related_products:
        print(product)
        product.save()

@receiver(post_save, sender=discount_code)
def generate_discount_code(sender, instance, created, **kwargs):
    from django.utils.crypto import get_random_string
    everyone_eligible = instance.eligible == 'everyone'
    if everyone_eligible:
        customers = SubscribedCustomers.objects.all()
        for each in customers:
            each.customer_discount_codes.add(instance)
    
    if not everyone_eligible:
        customers = SubscribedCustomers.objects.all()
        for each in customers:
            each.customer_discount_codes.remove(instance)

    if not instance.discount_code:
        instance.discount_code = str(get_random_string(length=8)).upper()
        instance.save()

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission.
        """
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has permission to view the app `app_label`.
        """
        return True

class AdvancedToken(Token):
    expires_at = models.DateTimeField(null=True, blank=True) 