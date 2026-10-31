from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BuyRequestForm, ListingForm
from reviews.views import review_context
from .models import BuyRequest, Category, Listing, ListingImage

def browse(request):
    listings = Listing.objects.public().select_related('category').prefetch_related('images')
    category = request.GET.get('category', '')
    listing_type = request.GET.get('type', '')
    search = request.GET.get('q', '')
    if category:
        listings = listings.filter(category__slug=category)
    if listing_type:
        listings = listings.filter(listing_type=listing_type)
    if search:
        listings = listings.filter(title__icontains=search)
    page = Paginator(listings, 9).get_page(request.GET.get('page'))
    query = request.GET.copy()
    query.pop('page', None)
    context = {
        'page': page,
        'categories': Category.objects.filter(is_active=True),
        'types': Listing.TYPE_CHOICES,
        'category': category,
        'listing_type': listing_type,
        'search': search,
        'query': query.urlencode(),
    }
    return render(request, 'catalog/browse.html', context)

def detail(request, pk):
    listing = get_object_or_404(Listing.objects.public(), pk=pk)
    my_request = None
    if request.user.is_authenticated:
        my_request = listing.requests.filter(buyer=request.user).first()
    context = {
        'listing': listing,
        'my_request': my_request,
        'is_seller': listing.seller == request.user,
        'request_form': BuyRequestForm(listing=listing),
    }
    context.update(review_context(request, listing))
    return render(request, 'catalog/detail.html', context)

@login_required
def new_listing(request):
    form = ListingForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        listing = form.save(commit=False)
        listing.seller = request.user
        listing.save()
        for position, photo in enumerate(request.FILES.getlist('photos')):
            ListingImage.objects.create(listing=listing, image=photo, position=position)
        messages.success(request, 'Listing submitted. It will appear after admin approval.')
        return redirect('my_listings')
    return render(request, 'catalog/new.html', {'form': form})

@login_required
def my_listings(request):
    listings = Listing.objects.filter(seller=request.user)
    return render(request, 'catalog/mine.html', {'listings': listings})

@login_required
def mark_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        listing.is_sold = True
        listing.save()
        messages.success(request, 'Listing marked as %s.' % listing.done_text().lower())
    return redirect('my_listings')
@login_required
def remove_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        for image in listing.images.all():
            image.image.delete(save=False)
        listing.delete()
        messages.success(request, 'Listing removed.')
        return redirect('my_listings')
    return render(request, 'catalog/remove.html', {'listing': listing})