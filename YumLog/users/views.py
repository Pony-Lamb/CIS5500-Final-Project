from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import users, restaurants, MenuDish, reviews, Match, Recipe
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import authenticate, login

# # 注册视图
# def register_view(request):
#     if request.method == 'POST':
#         # 复制 POST 数据（可修改）用于序列化校验
#         data = request.POST.copy()

#         # 用序列化器验证数据格式
#         serializer = RegisterSerializer(data=data)

#         if serializer.is_valid():
#             name = serializer.validated_data['username']
#             email = serializer.validated_data['email']

#             # 用户名或邮箱重复校验
#             if users.objects.filter(name=name).exists():
#                 return render(request, 'signup.html', {
#                     'errors': {'username': ['Username already exists']}
#                 })
#             if users.objects.filter(email=email).exists():
#                 return render(request, 'signup.html', {
#                     'errors': {'email': ['Email already exists']}
#                 })

#             # 获取标签字符串（由前端拼接的逗号分隔字符串）
#             tags_str = serializer.validated_data.get('tags', '')
#             tags_list = tags_str.split(',') if tags_str else []
#             tags_final = ','.join(tags_list)  # 可直接存储到数据库

#             # 创建用户并保存到数据库
#             users.objects.create(
#                 name=name,
#                 email=email,
#                 password=make_password(serializer.validated_data['password']),  # 加密密码
#                 tags=tags_final
#             )

#             # 注册成功后跳转到登录页面
#             return redirect('/login/')
#         else:
#             # 表单验证失败，重新渲染注册页并显示错误
#             return render(request, 'signup.html', {'errors': serializer.errors})

#     # GET 请求时渲染注册页面
#     return render(request, 'signup.html')


# # 登录视图
# def login_view(request):
#     if request.method == 'POST':
#         serializer = LoginSerializer(data=request.POST)
#         if serializer.is_valid():
#             email = serializer.validated_data['email']
#             password = serializer.validated_data['password']

#             try:
#                 user_obj = users.objects.get(email=email)
#                 user = authenticate(request, username=user_obj.username, password=password)
#             except  users.DoesNotExist:
#                 user = None

#             if user:
#                 login(request, user)  # ✅ Django 正式登录
#                 return redirect('index')
#             else:
#                 return render(request, 'login.html', {
#                     'errors': {'email': ['Invalid email or password']}
#                 })
#         else:
#             return render(request, 'login.html', {'errors': serializer.errors})
#     return render(request, 'login.html')

# 首页视图
def index_view(request):
    if request.session.get('is_logged_in'):
        return render(request, 'private_index.html')
    return render(request, 'public_index.html')


# 登录视图
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = users.objects.get(email=email)
            if check_password(password, user.password):
                # ✅ 手动设置 session 标记用户为已登录
                request.session['user_email'] = user.email
                request.session['is_logged_in'] = True
                request.session['username'] = user.name
                return redirect('private_index')
            else:
                return render(request, 'login.html', {'errors': {'password': ['Incorrect password']}})
        except users.DoesNotExist:
            return render(request, 'login.html', {'errors': {'email': ['User not found']}})

    return render(request, 'login.html')

# 注册视图
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        tags_str = request.POST.get('tags', '')  # ✅ 从前端表单获取 tags 字符串（可选）

        if users.objects.filter(name=username).exists():
            return render(request, 'signup.html', {'errors': {'username': ['Username already exists']}})
        if users.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'errors': {'email': ['Email already exists']}})

        # 处理 tags 字符串（如有逗号分隔）
        tags_list = tags_str.split(',') if tags_str else []
        tags_final = ','.join([tag.strip() for tag in tags_list])  # ✅ 去除多余空格再拼接

        users.objects.create(
            name=username,
            email=email,
            password=make_password(password),
            tags=tags_final  # ✅ 存入数据库
        )
        return redirect('login')

    return render(request, 'signup.html')

# 登出视图
def logout_view(request):
    request.session.flush()  # ✅ 清除所有 session 数据
    return redirect('public_index')


def profile_view(request):
    return render(request, 'profile.html')


# 首页展示视图（Discover Page）
def home_view(request):
    search_query = request.GET.get('q', '')  # 搜索关键词
    selected_tags = request.GET.getlist('tags')  # 搜索筛选标签

    restaurant = restaurants.objects.all()

    if search_query:
        restaurant = restaurant.filter(name__icontains=search_query)

    if selected_tags:
        restaurant = restaurant.filter(category__in=selected_tags)

    # 热门推荐：评分最高前 3 个
    trending_restaurants = restaurants.objects.order_by('-score')[:3]
 

    # # 精选评论：点赞数最多
    top_review = reviews.objects.order_by('-likes').first()

    # 个性化推荐逻辑：根据用户 tag 推荐类别匹配的餐厅
    recommended_restaurants = []
    if request.user.is_authenticated:
        try:
            user = users.objects.get(id=request.user.id)
            if user.tags:
                tag_list = [tag.strip() for tag in user.tags.split(',') if tag.strip()]
                recommended_restaurants = restaurants.objects.filter(category__in=tag_list).exclude(name="Ramen House")[:2]
        except users.DoesNotExist:
            pass

    context = {
        'restaurants': restaurant,
        'search_query': search_query,
        'selected_tags': selected_tags,
        'trending': trending_restaurants,
        'top_review': top_review,
        'recommended': recommended_restaurants
    }

    return render(request, 'private_index.html', context)


def restaurant_detail_view(request, restaurant_id):
    # 获取餐厅对象
    restaurant = get_object_or_404(restaurants, restaurant_id=restaurant_id)

    # 获取菜单菜品（OneToOne 改为 ForeignKey 时可返回多个）
    menu_dishes = MenuDish.objects.filter(restaurant=restaurant)

    # 获取该餐厅的所有评论（含点赞）
    review = reviews.objects.filter(restaurant=restaurant).order_by('-likes')

    # 获取菜品与食谱的匹配（Match 映射）
    matched_recipes = {
        match.menudish.name: match.recipe
        for match in Match.objects.filter(menudish__restaurant=restaurant)
    }

    context = {
        'restaurant': restaurant,
        'menu_dishes': menu_dishes,
        'review': review,
        'matched_recipes': matched_recipes
    }

    return render(request, 'restaurant_detail.html', context)

def discovery_view(request):
    return render(request, 'discovery.html')

def recommendations_view(request):
    return render(request, 'recommendations.html')


    # 社区页视图（Community Feed + Poll）
def community_view(request):
    # 获取最新的 10 条评论作为社区动态
    latest_reviews = reviews.objects.select_related('user', 'restaurant').order_by('-date')[:10]

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

    



