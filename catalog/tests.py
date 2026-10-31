from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import BuyRequest, Category, Listing


class ListingTest(TestCase):
    def setUp(self):
        self.student = User.objects.create(full_name='Rahim Khan', university_id='21101001', phone='01700000001', email='rahim@example.com')
        self.category = Category.objects.create(name='Phones', slug='phones')
        self.client.force_login(self.student)

    def test_post_then_approve(self):
        response = self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'rent', 'title': 'Calculator',
            'description': 'fx-991', 'price': '50', 'rent_period': 'day', 'condition': 'good',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Listing.objects.public().count(), 0)
        self.assertNotContains(self.client.get(reverse('browse')), 'Calculator')
        Listing.objects.update(status='approved')
        self.assertContains(self.client.get(reverse('browse')), 'Tk 50 / day')

    def test_rent_without_period_rejected(self):
        response = self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'rent', 'title': 'Bat',
            'description': 'x', 'price': '50', 'condition': 'good',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)

    def test_donate_is_free_and_marked_donated(self):
        self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'donate', 'title': 'Old book',
            'description': 'x', 'price': '99', 'condition': 'good',
        })
        listing = Listing.objects.get()
        self.assertIsNone(listing.price)
        Listing.objects.update(status='approved')
        self.assertContains(self.client.get(reverse('browse')), 'Free')
        self.client.post(reverse('mark_sold', args=[listing.pk]))
        self.assertContains(self.client.get(reverse('my_listings')), 'Donated')


class BuyReviewTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create(full_name='Seller', university_id='1', phone='01700000010', email='s@example.com')
        self.buyer = User.objects.create(full_name='Buyer', university_id='2', phone='01700000011', email='b@example.com')
        category = Category.objects.create(name='Phones', slug='phones')
        self.listing = Listing.objects.create(
            seller=self.seller, category=category, title='Phone', description='x', listing_type='sell',
            price=500, condition='good', status='approved',
        )

    def test_contact_hidden_until_request_then_seller_accepts(self):
        self.client.force_login(self.buyer)
        url = reverse('detail', args=[self.listing.pk])
        self.assertNotContains(self.client.get(url), '01700000010')
        self.client.post(reverse('request_buy', args=[self.listing.pk]), {'amount': ''})
        self.assertEqual(self.listing.requests.count(), 0)
        self.client.post(reverse('request_buy', args=[self.listing.pk]), {'amount': '450'})
        page = self.client.get(url)
        self.assertContains(page, '01700000010')
        self.assertContains(page, 'Tk 450')
        self.client.force_login(self.seller)
        buy_request = self.listing.requests.get()
        self.assertContains(self.client.get(reverse('listing_requests', args=[self.listing.pk])), '450')
        self.client.post(reverse('accept_request', args=[buy_request.pk]))
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_sold)

    def test_cannot_accept_after_sold(self):
        other = User.objects.create(full_name='Other', university_id='3', phone='01700000012', email='o@example.com')
        first = BuyRequest.objects.create(listing=self.listing, buyer=self.buyer, amount=450)
        second = BuyRequest.objects.create(listing=self.listing, buyer=other, amount=480)
        self.client.force_login(self.seller)
        self.client.post(reverse('accept_request', args=[first.pk]))
        self.client.post(reverse('accept_request', args=[second.pk]))
        second.refresh_from_db()
        self.assertEqual(second.status, 'pending')
