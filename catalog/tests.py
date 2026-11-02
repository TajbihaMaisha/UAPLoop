from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
            'description': 'fx-991', 'handover_place': 'UAP main gate',
            'price': '50', 'rent_period': 'day', 'condition': 'good',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Listing.objects.public().count(), 0)
        self.assertNotContains(self.client.get(reverse('browse')), 'Calculator')
        Listing.objects.update(status='approved')
        self.assertContains(self.client.get(reverse('browse')), 'Tk 50 / day')

    def test_rent_without_period_rejected(self):
        response = self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'rent', 'title': 'Bat',
            'description': 'x', 'handover_place': 'UAP main gate', 'price': '50', 'condition': 'good',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Listing.objects.count(), 0)

    def test_new_listing_requires_handover_place(self):
        response = self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'sell', 'title': 'Calculator',
            'description': 'fx-991', 'price': '500', 'condition': 'good',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'handover_place', 'This field is required.')
        self.assertEqual(Listing.objects.count(), 0)

    def test_handover_place_is_saved_and_shown_on_listing_pages(self):
        response = self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'sell', 'title': 'Calculator',
            'description': 'fx-991', 'price': '500', 'condition': 'good',
            'handover_place': 'UAP main gate',
        })
        self.assertEqual(response.status_code, 302)
        listing = Listing.objects.get()
        self.assertEqual(listing.handover_place, 'UAP main gate')
        listing.status = 'approved'
        listing.save()
        self.assertContains(self.client.get(reverse('browse')), 'UAP main gate')
        self.assertContains(self.client.get(reverse('detail', args=[listing.pk])), 'UAP main gate')

    def test_donate_is_free_and_marked_donated(self):
        self.client.post(reverse('new_listing'), {
            'category': self.category.pk, 'listing_type': 'donate', 'title': 'Old book',
            'description': 'x', 'handover_place': 'UAP main gate', 'price': '99', 'condition': 'good',
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
            handover_place='UAP main gate', price=500, condition='good', status='approved',
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


class EditListingTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create(full_name='Seller', university_id='1', phone='01700000010', email='s@example.com')
        self.other = User.objects.create(full_name='Other', university_id='2', phone='01700000011', email='o@example.com')
        self.category = Category.objects.create(name='Phones', slug='phones')
        self.listing = Listing.objects.create(
            seller=self.seller, category=self.category, title='Old title', description='x', listing_type='sell',
            handover_place='UAP main gate', price=500, condition='good', status='approved', reviewed_by=self.other,
            reviewed_at=timezone.now(),
        )
        self.url = reverse('edit_listing', args=[self.listing.pk])
        self.client.force_login(self.seller)

    def form_data(self, **changes):
        data = {
            'category': self.category.pk, 'listing_type': 'sell', 'title': 'Old title', 'description': 'x',
            'handover_place': 'UAP main gate', 'price': '500', 'condition': 'good',
        }
        data.update(changes)
        return data

    def test_form_opens_with_current_values(self):
        self.assertContains(self.client.get(self.url), 'value="Old title"')

    def test_change_hides_listing_until_approved_again(self):
        response = self.client.post(self.url, self.form_data(title='New title'))
        self.assertRedirects(response, reverse('my_listings'))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'New title')
        self.assertEqual(self.listing.status, 'pending')
        self.assertIsNone(self.listing.reviewed_by)
        self.assertIsNone(self.listing.reviewed_at)
        self.assertNotContains(self.client.get(reverse('browse')), 'New title')
        self.assertEqual(self.client.get(reverse('detail', args=[self.listing.pk])).status_code, 404)
        Listing.objects.update(status='approved')
        self.assertContains(self.client.get(reverse('browse')), 'New title')

    def test_edit_clears_reject_reason(self):
        Listing.objects.update(status='rejected', reject_reason='Blurry')
        self.client.post(self.url, self.form_data(description='Better details'))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, 'pending')
        self.assertEqual(self.listing.reject_reason, '')

    def test_save_without_changes_keeps_approval(self):
        self.client.post(self.url, self.form_data())
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, 'approved')
        self.assertIsNotNone(self.listing.reviewed_at)

    def test_invalid_edit_changes_nothing(self):
        response = self.client.post(self.url, self.form_data(title='New title', listing_type='rent'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'rent_period', 'Rent period is required.')
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Old title')
        self.assertEqual(self.listing.status, 'approved')

    def test_seller_cannot_approve_by_posting_status(self):
        Listing.objects.update(status='rejected')
        self.client.post(self.url, self.form_data(title='New title', status='approved', seller=self.other.pk))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, 'pending')
        self.assertEqual(self.listing.seller, self.seller)

    def test_only_seller_can_edit(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.form_data(title='Hacked')).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.post(self.url, self.form_data(title='Hacked'), follow=True).status_code, 401)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Old title')

    def test_sold_listing_cannot_be_edited(self):
        self.assertContains(self.client.get(reverse('my_listings')), self.url)
        Listing.objects.update(is_sold=True)
        self.assertNotContains(self.client.get(reverse('my_listings')), self.url)
        self.assertRedirects(self.client.post(self.url, self.form_data(title='New title')), reverse('my_listings'))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'Old title')
        self.assertEqual(self.listing.status, 'approved')

    def test_hidden_category_stays_selectable_on_own_listing(self):
        Category.objects.update(is_active=False)
        self.client.post(self.url, self.form_data(title='New title'))
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.title, 'New title')
        self.assertEqual(self.client.post(reverse('new_listing'), self.form_data(title='Another')).status_code, 200)
        self.assertEqual(Listing.objects.count(), 1)

    def test_chat_hides_view_item_while_listing_is_pending(self):
        buy_request = BuyRequest.objects.create(listing=self.listing, buyer=self.other, amount=450)
        chat_url = reverse('conversation', args=[buy_request.pk])
        detail_url = reverse('detail', args=[self.listing.pk])
        self.assertContains(self.client.get(chat_url), detail_url)
        self.client.post(self.url, self.form_data(title='New title'))
        self.assertNotContains(self.client.get(chat_url), detail_url)
