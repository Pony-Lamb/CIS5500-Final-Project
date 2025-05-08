from django.urls import path
from . import views
from .views import (
    register_view,
    login_view,
    home_view,
    restaurant_detail_view,
    restaurant_map_view,
    community_view,
    recipe_detail_view,  
    public_index,
    profile_view,
    logout_view, 
    restaurant_list_view,
    recipe_detail_view,
    toggle_like_view,
    update_tags_view,
    submit_review,
    delete_review,
    google_transfer_view,
)

urlpatterns = [
    path('', public_index, name='public_index'), 
    path('register/', register_view, name='register'),  # 注册页面
    path('transfer/', views.google_transfer_view, name='google_transfer'), # google sign in transfer page
    path('profile/', profile_view, name='profile'),  # 注册页面
    path('login/', login_view, name='login'),  # 登录页面
    path('private_index/', home_view, name='private_index'),  # 登录后首页
    path('restaurant/<int:restaurant_id>/', restaurant_detail_view, name='restaurant_detail'),  # 餐厅详情页
    path('restaurant/<int:restaurant_id>/map/', restaurant_map_view, name='restaurant_map'),  # 餐厅地图页
    path('community/', community_view, name='community'),  # 社区页面（社区动态 + 投票）
    #path('recipe/<int:recipe_id>/', recipe_detail_view, name='recipe_detail'),  # 食谱详情页
    path('public_index/', logout_view, name='logout'),  # 食谱详情页
    path('discovery/', restaurant_list_view, name='discovery'),  # 🌟 餐厅筛选页面
    path('recipe/<int:recipe_id>/', recipe_detail_view, name='recipe_detail'),
    path('toggle_like/<int:review_id>/', toggle_like_view, name='toggle_like'),
    path('update_tags/', update_tags_view, name='update_tags'),
    path('restaurant/<int:restaurant_id>/submit_review/', submit_review, name='submit_review'),
    path('delete_review/<int:review_id>/', delete_review, name='delete_review'),
    path('transfer/', google_transfer_view, name='google_transfer'),

    
    
]


