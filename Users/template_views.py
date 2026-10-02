from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import SignupForm


def signup_view(request):
    if request.method == 'POST':
        # request.FILES needed here because of display_picture (file upload)
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the user in immediately after signup
            return redirect('product-list-page')
    else:
        form = SignupForm()

    return render(request, 'Users/signup.html', {'form': form})

@login_required
def profile_page(request):
    return render(request, 'Users/profile.html')