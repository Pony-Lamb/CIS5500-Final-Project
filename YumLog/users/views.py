from django.shortcuts import render

# Create your views here.

def toLogin_view(request):
    return render(request,'login.html')

def Login_view(request):
    userName=request.POST.get("user",'')
    password=request.POST.get("pwd",'')

    if userName and password:
        return HttpResponse("Login successful!")
    else:
        return HttpResponse("Login failed!")
