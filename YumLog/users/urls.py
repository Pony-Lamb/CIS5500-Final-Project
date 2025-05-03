from django.urls import path
from .views import (
    register_view,
    login_view,
    home_view,
    restaurant_detail_view,
    restaurant_map_view,
    community_view,
    recipe_detail_view,  
)

urlpatterns = [
    path('register/', register_view, name='register'),  # 注册页面
    path('login/', login_view, name='login'),  # 登录页面
    path('dashboard/', home_view, name='dashboard'),  # 登录后首页（Discover 页面）
    path('restaurant/<int:restaurant_id>/', restaurant_detail_view, name='restaurant_detail'),  # 餐厅详情页
    path('restaurant/<int:restaurant_id>/map/', restaurant_map_view, name='restaurant_map'),  # 餐厅地图页
    path('community/', community_view, name='community'),  # 社区页面（社区动态 + 投票）
    path('recipe/<int:recipe_id>/', recipe_detail_view, name='recipe_detail'),  # 食谱详情页
]

