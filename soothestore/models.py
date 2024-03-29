from django.db import models
from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

def RetrieveDate(Raw_Date):
    day = Raw_Date.day
    month = Raw_Date.month
    year = Raw_Date.year
    return day, month, year

class ChairFeature(models.Model):
    called = models.CharField(max_length=50, default=None)
    feature_description = models.CharField(max_length=255, default=None, blank=True, null=True)
    feature_showcase = models.ImageField(default=None, blank=True, null=True)
    def __str__(self):
        return str(self.called)

class ChairType(models.Model):
    called = models.CharField(max_length=60)
    def __str__(self):
        return str(self.called)

class Brand(models.Model):
    brand_name = models.CharField(max_length=20)
    authorized_in = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.brand_name)

class MassageChair(models.Model):
    title = models.CharField(max_length=35)
    brand = models.ForeignKey(Brand, on_delete=models.DO_NOTHING)
    brand_name = models.CharField(max_length=20, blank=True, default="No Brand")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    description = models.TextField(default=None)
    available_colors = models.ManyToManyField('Color_Options', related_name='massage_chairs')
    features = models.ManyToManyField(ChairFeature, related_name='Massage_Features')
    purchased = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.6, validators=[MaxValueValidator(limit_value=5.0)])
    posted = models.DateTimeField(default=timezone.now)

    def color_options(self):
        colors = self.available_colors.all()
        return [[str(color.color_name), str(color.color_code), str(color.image.url)] for color in colors]
    
    def chair_features(self):
        features = self.features.all()
        return [str(feature.called) for feature in features]
    
    def posted(self):
        return 'today'

    def save(self, *args, **kwargs):
        self.brand_name = self.brand.brand_name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

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
    review_text = models.TextField(default=None)
    posted_date = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'Review By {str(self.id)}'

class ReviewResponse(models.Model):
    responded_to = models.ForeignKey(ChairReview, on_delete=models.CASCADE)
    poster = models.CharField(max_length=35, default='Massage Chairs')
    response_text = models.TextField(default='')
    responded_date = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f'Review Response by Business'

class Color_Options(models.Model):
    color_name = models.CharField(max_length=50, unique=True)
    color_code = models.TextField()
    image = models.ImageField(default=None, blank=True, null=True)

    def __str__(self):
        return self.image.url
    
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