from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from catalog.models import Listing
from .forms import ReviewForm


def review_context(request, listing):
    my_review = None
    can_review = False
    if request.user.is_authenticated:
        my_review = listing.reviews.filter(reviewer=request.user).first()
        verified = listing.requests.filter(buyer=request.user, status='accepted').exists()
        can_review = verified and my_review is None
    return {
        'reviews': listing.reviews.public().select_related('reviewer'),
        'my_review': my_review,
        'can_review': can_review,
        'review_form': ReviewForm(),
    }


@login_required
def add_review(request, pk):
    listing = get_object_or_404(Listing.objects.public(), pk=pk)
    if request.method == 'POST' and review_context(request, listing)['can_review']:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.listing = listing
            review.reviewer = request.user
            review.save()
            messages.success(request, 'Review submitted. It will appear after admin approval.')
    return redirect('detail', pk=pk)
