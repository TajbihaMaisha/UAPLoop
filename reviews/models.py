from django.conf import settings
from django.db import models

from catalog.models import ApprovedQuerySet, Listing


class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(n, '★' * n + '☆' * (5 - n)) for n in range(1, 6)])
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Listing.STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ApprovedQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['listing', 'reviewer'], name='one_review_per_buyer')]
