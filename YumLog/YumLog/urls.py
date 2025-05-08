"""
URL configuration for YumLog project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from users.views import home_view, login_view, public_index, restaurant_list_view, community_view, smart_recs_view, register_view,  index_view, google_transfer_view, CustomSocialSignupView, recipe_detail_view
from django.urls import path, include   

urlpatterns = [
    path('', public_index, name='public_index'),
    path("admin/", admin.site.urls),

    # Override the social-signup URL:
    path(
        'accounts/3rdparty/signup/',
        CustomSocialSignupView.as_view(),
        name='socialaccount_signup'
    ),
    # Then include the rest of the socialaccount URLs
    path('accounts/', include('allauth.urls')),

    path("transfer/", google_transfer_view, name="google_transfer"),
    path("users/", include('users.urls')),
    path("signup/", register_view, name='signup'),
    path("login/", login_view, name='login'), 
    #path("private_index/", home_view, name='private_index'), 
    path('discovery/', restaurant_list_view, name='discovery'), 
    path('community/', community_view, name='community'),
    path('smart_recs/', smart_recs_view, name='smart_recs'),
    path('recipe/', recipe_detail_view, name='recipe'),
    path('index/', index_view, name='index'),

]


