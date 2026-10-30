import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class ApprovedQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status='approved')


class Listing(models.Model):
    TYPE_CHOICES = [('sell', 'Sell'), ('exchange', 'Exchange'), ('rent', 'Rent'), ('donate', 'Donate')]
    PERIOD_CHOICES = [('day', 'Day'), ('week', 'Week'), ('month', 'Month')]
    CONDITION_CHOICES = [('new', 'New'), ('like_new', 'Like new'), ('good', 'Good'), ('fair', 'Fair')]
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='listings')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    title = models.CharField(max_length=120)
    description = models.TextField()
    listing_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rent_period = models.CharField(max_length=10, choices=PERIOD_CHOICES, null=True, blank=True)
    exchange_for = models.CharField(max_length=200, blank=True)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reject_reason = models.TextField(blank=True)
    is_sold = models.BooleanField(default=False)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_listings'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ApprovedQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['category', 'status']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(listing_type__in=['exchange', 'donate']) | models.Q(price__isnull=False),
                name='sell_rent_need_price',
            ),
            models.CheckConstraint(
                condition=~models.Q(listing_type='rent') | models.Q(rent_period__isnull=False),
                name='rent_needs_period',
            ),
        ]

    def __str__(self):
        return self.title

    def cover(self):
        return self.images.first()

    def done_text(self):
        return {'donate': 'Donated', 'exchange': 'Exchanged'}.get(self.listing_type, 'Sold')

    def price_text(self):
        if self.listing_type == 'donate':
            return 'Free'
        if self.price is None:
            return ''
        text = 'Tk %d' % self.price
        if self.listing_type == 'rent':
            text += ' / ' + self.rent_period
        return text


def image_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower()
    return 'listings/%s/%s.%s' % (instance.listing_id, uuid.uuid4().hex, extension)


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=image_path)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']


class BuyRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted')]

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='requests')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buy_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['listing', 'buyer'], name='one_request_per_buyer')]
