from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import BuyRequest, Category, Listing


class InboxTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create(full_name='Seller', university_id='1', phone='01700000010', email='s@example.com')
        self.buyer = User.objects.create(full_name='Buyer', university_id='2', phone='01700000011', email='b@example.com')
        self.other = User.objects.create(full_name='Other', university_id='3', phone='01700000012', email='o@example.com')
        category = Category.objects.create(name='Phones', slug='phones')
        self.listing = Listing.objects.create(
            seller=self.seller, category=category, title='Phone', description='x', listing_type='sell',
            price=500, condition='good', status='approved',
        )
        self.buy_request = BuyRequest.objects.create(listing=self.listing, buyer=self.buyer, amount=450)
        self.url = reverse('conversation', args=[self.buy_request.pk])

    def test_buyer_and_seller_chat(self):
        self.client.force_login(self.buyer)
        self.assertContains(self.client.get(reverse('inbox')), 'Phone')
        self.client.post(self.url, {'text': 'Is it available?'})
        self.client.force_login(self.seller)
        self.assertContains(self.client.get(reverse('inbox')), 'Phone')
        self.assertContains(self.client.get(self.url), 'Is it available?')
        self.client.post(self.url, {'text': 'Yes'})
        self.assertEqual(self.buy_request.messages.count(), 2)

    def test_outsider_cannot_open_or_post(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('inbox')), 'Phone')
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.post(self.url, {'text': 'hi'})
        self.assertEqual(self.buy_request.messages.count(), 0)

    def test_anonymous_gets_401(self):
        self.assertEqual(self.client.get(reverse('inbox'), follow=True).status_code, 401)

    def test_new_messages_returns_only_newer_ones(self):
        first = self.buy_request.messages.create(sender=self.buyer, text='one')
        self.buy_request.messages.create(sender=self.seller, text='two')
        self.client.force_login(self.buyer)
        url = reverse('new_messages', args=[self.buy_request.pk])
        data = self.client.get(url, {'after': first.id}).json()
        self.assertEqual([m['text'] for m in data['messages']], ['two'])
        self.assertFalse(data['messages'][0]['mine'])
        self.assertEqual(len(self.client.get(url).json()['messages']), 2)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
