from django import forms

from config.forms import add_bootstrap
from .models import BuyRequest, Category, Listing

MAX_PHOTOS = 5
MAX_SIZE = 5 * 1024 * 1024


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['category', 'listing_type', 'title', 'description', 'price', 'rent_period', 'exchange_for', 'condition']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['price'].label = 'Price (Tk)'
        self.fields['rent_period'].help_text = 'Only for rent'
        self.fields['exchange_for'].help_text = 'Only for exchange'
        add_bootstrap(self)

    def clean(self):
        data = super().clean()
        listing_type = data.get('listing_type')
        if listing_type in ('sell', 'rent') and data.get('price') is None:
            self.add_error('price', 'Price is required.')
        if listing_type == 'rent' and not data.get('rent_period'):
            self.add_error('rent_period', 'Rent period is required.')
        if listing_type == 'exchange' and not data.get('exchange_for'):
            self.add_error('exchange_for', 'Say what you want in exchange.')
        if listing_type != 'rent':
            data['rent_period'] = None
        if listing_type in ('exchange', 'donate'):
            data['price'] = None
        photos = self.files.getlist('photos')
        if len(photos) > MAX_PHOTOS:
            raise forms.ValidationError('Upload at most %d photos.' % MAX_PHOTOS)
        for photo in photos:
            if photo.size > MAX_SIZE:
                raise forms.ValidationError('Each photo must be 5 MB or smaller.')
            forms.ImageField().clean(photo)
        return data


class BuyRequestForm(forms.ModelForm):
    class Meta:
        model = BuyRequest
        fields = ['amount']
        labels = {'amount': 'Amount you want to buy for (Tk)'}

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        add_bootstrap(self)

    def clean(self):
        data = super().clean()
        if self.listing.listing_type in ('sell', 'rent'):
            if data.get('amount') is None:
                self.add_error('amount', 'Enter the amount.')
        else:
            data['amount'] = None
        return data
