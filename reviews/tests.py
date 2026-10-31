from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import BuyRequest, Category, Listing
from .models import Review


class ReviewTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create(full_name='Seller', university_id='1', phone='01700000010', email='s@example.com')
        self.buyer = User.objects.create(full_name='Buyer', university_id='2', phone='01700000011', email='b@example.com')
        category = Category.objects.create(name='Phones', slug='phones')
        self.listing = Listing.objects.create(
            seller=self.seller, category=category, title='Phone', description='x', listing_type='sell',
            price=500, condition='good', status='approved',
        )
        self.url = reverse('detail', args=[self.listing.pk])
        self.review_url = reverse('add_review', args=[self.listing.pk])
        self.review = {'rating': 5, 'comment': 'great'}
        self.client.force_login(self.buyer)

    def test_unverified_buyer_cannot_review(self):
        BuyRequest.objects.create(listing=self.listing, buyer=self.buyer, amount=450)
        self.client.post(self.review_url, self.review)
        self.assertEqual(Review.objects.count(), 0)

    def test_verified_review_needs_admin_approval(self):
        BuyRequest.objects.create(listing=self.listing, buyer=self.buyer, amount=450, status='accepted')
        self.client.post(self.review_url, self.review)
        self.client.post(self.review_url, self.review)
        self.assertEqual(Review.objects.count(), 1)
        self.assertContains(self.client.get(self.url), 'once an admin approves')
        self.assertNotContains(self.client.get(self.url), 'great')
        self.client.logout()
        self.assertNotContains(self.client.get(self.url), 'great')
        Review.objects.update(status='approved')
        self.assertContains(self.client.get(self.url), 'great')
