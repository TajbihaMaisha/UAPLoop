from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from catalog.models import BuyRequest
from .forms import MessageForm


def my_conversations(user):
    mine = Q(buyer=user) | Q(listing__seller=user)
    return BuyRequest.objects.filter(mine).select_related('listing', 'buyer', 'listing__seller')


@login_required
def inbox(request):
    conversations = my_conversations(request.user).annotate(last=Max('messages__created_at')).order_by('-last', '-created_at')
    return render(request, 'inbox/inbox.html', {'conversations': conversations})


@login_required
def conversation(request, pk):
    buy_request = get_object_or_404(my_conversations(request.user), pk=pk)
    form = MessageForm(request.POST or None)
    if form.is_valid():
        message = form.save(commit=False)
        message.buy_request = buy_request
        message.sender = request.user
        message.save()
        return redirect('conversation', pk=pk)
    other = buy_request.listing.seller if buy_request.buyer == request.user else buy_request.buyer
    context = {
        'buy_request': buy_request,
        'other': other,
        'chat_messages': buy_request.messages.select_related('sender'),
        'last_id': buy_request.messages.aggregate(last=Max('id'))['last'] or 0,
        'form': form,
    }
    return render(request, 'inbox/conversation.html', context)


@login_required
def new_messages(request, pk):
    buy_request = get_object_or_404(my_conversations(request.user), pk=pk)
    after = request.GET.get('after', '')
    after = int(after) if after.isdigit() else 0
    found = []
    for message in buy_request.messages.filter(id__gt=after).select_related('sender'):
        found.append({
            'id': message.id,
            'name': 'You' if message.sender == request.user else message.sender.full_name,
            'mine': message.sender == request.user,
            'time': timezone.localtime(message.created_at).strftime('%d %b, %H:%M'),
            'text': message.text,
        })
    return JsonResponse({'messages': found})
