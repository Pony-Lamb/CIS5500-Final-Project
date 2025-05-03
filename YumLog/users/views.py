from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Restaurant, MenuDish, Review, Match, Recipe
from .serializers import RegisterSerializer, LoginSerializer

# 注册视图
def register_view(request):
    if request.method == 'POST':
        # 复制 POST 数据 + 提取标签（button 形式的 tags[] 会传多个同名字段）
        data = request.POST.copy()
        data.setlist('tags', request.POST.getlist('tags'))

        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            name = serializer.validated_data['username']
            email = serializer.validated_data['email']

            # 用户名或邮箱重复校验
            if User.objects.filter(name=name).exists():
                return render(request, 'register.html', {'errors': {'username': ['Username already exists']}})
            if User.objects.filter(email=email).exists():
                return render(request, 'register.html', {'errors': {'email': ['Email already exists']}})

            # 获取标签并转为字符串存储
            tags_list = serializer.validated_data.get('tags', [])
            tags_str = ",".join(tags_list)

            # 创建用户
            User.objects.create(
                name=name,
                email=email,
                password=make_password(serializer.validated_data['password']),
                tags=tags_str
            )

            return redirect('/login/')
        else:
            return render(request, 'register.html', {'errors': serializer.errors})
    return render(request, 'register.html')


# 登录视图
def login_view(request):
    if request.method == 'POST':
        serializer = LoginSerializer(data=request.POST)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(email=email)
                if check_password(password, user.password):
                    # 登录成功 → 跳转主页或记录 session（可扩展）
                    return redirect('/dashboard/')
                else:
                    return render(request, 'login.html', {'errors': {'password': ['Incorrect password']}})
            except User.DoesNotExist:
                return render(request, 'login.html', {'errors': {'email': ['User not found']}})
        else:
            return render(request, 'login.html', {'errors': serializer.errors})
    return render(request, 'login.html')


# 首页展示视图（Discover Page）
def home_view(request):
    search_query = request.GET.get('q', '')  # 搜索关键词
    selected_tags = request.GET.getlist('tags')  # 搜索筛选标签

    restaurants = Restaurant.objects.all()

    if search_query:
        restaurants = restaurants.filter(name__icontains=search_query)

    if selected_tags:
        restaurants = restaurants.filter(category__in=selected_tags)

    # 热门推荐：评分最高前 3 个
    trending_restaurants = Restaurant.objects.order_by('-score')[:3]

    # 精选评论：点赞数最多
    top_review = Review.objects.order_by('-likes').first()

    # 个性化推荐逻辑：根据用户 tag 推荐类别匹配的餐厅
    recommended_restaurants = []
    if request.user.is_authenticated:
        try:
            user = User.objects.get(id=request.user.id)
            if user.tags:
                tag_list = [tag.strip() for tag in user.tags.split(',') if tag.strip()]
                recommended_restaurants = Restaurant.objects.filter(category__in=tag_list).exclude(name="Ramen House")[:2]
        except User.DoesNotExist:
            pass

    context = {
        'restaurants': restaurants,
        'search_query': search_query,
        'selected_tags': selected_tags,
        'trending': trending_restaurants,
        'top_review': top_review,
        'recommended': recommended_restaurants
    }

    return render(request, 'home.html', context)


def restaurant_detail_view(request, restaurant_id):
    # 获取餐厅对象
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)

    # 获取菜单菜品（OneToOne 改为 ForeignKey 时可返回多个）
    menu_dishes = MenuDish.objects.filter(restaurant=restaurant)

    # 获取该餐厅的所有评论（含点赞）
    reviews = Review.objects.filter(restaurant=restaurant).order_by('-likes')

    # 获取菜品与食谱的匹配（Match 映射）
    matched_recipes = {
        match.menudish.name: match.recipe
        for match in Match.objects.filter(menudish__restaurant=restaurant)
    }

    context = {
        'restaurant': restaurant,
        'menu_dishes': menu_dishes,
        'reviews': reviews,
        'matched_recipes': matched_recipes
    }

    return render(request, 'restaurant_detail.html', context)


    # 社区页视图（Community Feed + Poll）
def community_view(request):
    # 获取最新的 10 条评论作为社区动态
    latest_reviews = Review.objects.select_related('user', 'restaurant').order_by('-date')[:10]

    # 模拟投票选项（可改为数据库模型）
    poll_question = "What's the best sushi spot in NYC?"
    poll_options = ["Sushi Nakazawa", "Sushi Yasuda", "Sugarfish"]

    # 话题标签（可改为动态）
    explore_topics = ["Ramen Spots", "Cheap Eats", "Top Rated"]

    context = {
        'reviews': latest_reviews,
        'poll_question': poll_question,
        'poll_options': poll_options,
        'topics': explore_topics
    }
    return render(request, 'community.html', context)

# 获取餐厅信息
def restaurant_map_view(request, restaurant_id):

    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)

    context = {
        'restaurant': restaurant,
        'latitude': restaurant.latitude,
        'longitude': restaurant.longitude,
    }

    return render(request, 'restaurant_map.html', context)


def recipe_detail_view(request, recipe_id):
    # 获取当前 Recipe 对象
    recipe = get_object_or_404(Recipe, recipe_id=recipe_id)

    # 获取其它推荐 Recipe（Matched Recipes）
    matched_recipes = Recipe.objects.exclude(recipe_id=recipe_id)[:3]  # 简单逻辑：展示除本身以外的前 3 条，可替换为 NLP 结果

    # 获取当前 Recipe 匹配到的所有 MenuDish（即：在哪些餐厅有类似的菜）
    matched_menu_dishes = Match.objects.filter(recipe=recipe)

    # 获取菜品所属餐厅信息
    similar_restaurants = [match.menudish.restaurant for match in matched_menu_dishes]

    context = {
        'recipe': recipe,                         # 当前菜谱对象
        'matched_recipes': matched_recipes,       # 相关推荐菜谱
        'similar_restaurants': similar_restaurants  # 相似餐厅（从匹配菜品中提取）
    }

    return render(request, 'recipe_detail.html', context)

    



