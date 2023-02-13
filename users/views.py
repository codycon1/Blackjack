from django.shortcuts import render

# Create your views here.
def user_signup(request):
    if request.method == 'POST':
        form = BlackjackUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = BlackjackUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})