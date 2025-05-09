from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import users, restaurants, menudishes, reviews, match, recipes
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import authenticate, login
from django.db.models import Q
from allauth.socialaccount.views import SignupView
from django.urls import reverse
from django.db import connection
import re
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.db.models import F, FloatField, ExpressionWrapper
from django.db.models.functions import ACos, Cos, Radians, Sin
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import datetime
from datetime import date
from django.db import connection


# 首页视图
def index_view(request):
    if request.session.get('is_logged_in'):
        return home_view(request)
    return public_index(request)


# 登录视图
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = users.objects.get(email=email)
            if password == user.password or check_password(password, user.password):
                # ✅ 手动设置 session 标记用户为已登录
                request.session['user_email'] = user.email
                request.session['is_logged_in'] = True
                request.session['username'] = user.name
                return redirect('index')
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

        num = users.objects.count()
        id = 'u' + str(num)
        users.objects.create(
            user_id=id,
            name=username,
            email=email,
            password=make_password(password),
            tags=tags_final,
            profile='',
            city='',
            state=''
        )
        return redirect('login')

    return render(request, 'signup.html')

# 登出视图

def logout_view(request):
    request.session.flush()  # ✅ 清除所有 session 数据
    return redirect('index')

ALL_TAGS = [
    "American", "Burgers", "Fast Food", "Mexican", "Asian",
    "Pizza", "Desserts", "Seafood", "Sushi", "Vegetarian Friendly"
]

def profile_view(request):
    # if request.session.get('is_logged_in'):
    email = request.session.get('user_email', 'yongyinyang0418@gmail.com')
    reviews = []
    username = ""
    tags = []

    try:
        cur = connection.cursor()

        # 获取用户名和当前标签
        cur.execute("SELECT u.name, u.tags FROM users u WHERE u.email = %s;", [email])
        row = cur.fetchone()

        if row:
            username = row[0] if row[0] else "sheepMie"
            tags = row[1].split(',') if row[1] else ["American"]
            print(f"[DEBUG] Found user: name={username}, tags={tags}")
        else:
            username = "sheepMie"
            tags = ["American"]
            print(f"[DEBUG] No user found for {email}. Using default values.")

        # ✅ 获取用户的评论
        cur.execute("""
            SELECT r.review_id, r.text, r.likes, r.stars, r.date, rest.name 
            FROM users u 
            JOIN reviews r ON u.user_id = r.user_id 
            JOIN restaurants rest ON rest.restaurant_id = r.restaurant_id 
            WHERE u.email = %s
            ORDER BY r.date DESC;
        """, [email])

        rows = cur.fetchall()
        for row in rows:
            reviews.append({
                'review_id': row[0],
                'text': row[1],
                'likes': row[2],
                'stars': row[3],
                'date': row[4],
                'restaurant': row[5],
            })

        cur.close()

    except Exception as e:
        print("[ERROR] Database connection failed:", e)
        username = "sheepMie"
        tags = ["American"]

    print(f"[RESULT] username={username}, tags={tags}, review_count={len(reviews)}")

    return render(request, 'profile.html', {
        'username': username,
        'email': email,
        'tags': tags,
        'all_tags': ALL_TAGS,
        'reviews': reviews
    })

    return redirect('login')





def update_tags_view(request):
    if request.method == 'POST' and request.session.get('user_email'):
        email = request.session['user_email']
        selected_tags = request.POST.getlist("tags")
        tags_str = ",".join(selected_tags)

        try:
            cur = connection.cursor()
            cur.execute("UPDATE users SET tags = %s WHERE email = %s;", [tags_str, email])
            connection.commit()  # ✅ 添加这一行
            cur.close()
            print(f"[SUCCESS] Updated tags to {tags_str} for {email}")
        except Exception as e:
            print("[ERROR] Failed to update tags: ", e)

    return redirect('profile')




def submit_review(request, restaurant_id):
    if request.method == 'POST' and request.session.get('is_logged_in'):
        text = request.POST.get('text')
        stars = float(request.POST.get('stars'))
        email = request.session.get('user_email')

        try:
            user = users.objects.get(email=email)
            restaurant = restaurants.objects.get(restaurant_id=restaurant_id)

            # ❗手动生成唯一 review_id（不要用于高并发生产环境）
            cur = connection.cursor()
            cur.execute("SELECT MAX(review_id) FROM reviews;")
            max_id = cur.fetchone()[0] or 0
            next_id = max_id + 1
            cur.close()

            # 插入评论（显式指定 review_id）
            reviews.objects.create(
                review_id=next_id,
                user=user,
                restaurant=restaurant,
                text=text,
                stars=stars,
                likes=0,
                date=date.today()
            )

        except Exception as e:
            print("插入评论失败：", e)

    return redirect('restaurant_detail', restaurant_id=restaurant_id)


from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def delete_review(request, review_id):
    if request.method == 'POST' and request.session.get('is_logged_in'):
        try:
            email = request.session['user_email']
            user = users.objects.get(email=email)
            review = reviews.objects.get(review_id=review_id)

            if review.user.user_id == user.user_id:
                review.delete()
        except Exception as e:
            print("删除失败：", e)

    return redirect(request.META.get('HTTP_REFERER', '/'))

# def profile_view(request):
#     # reviews = []
#     # email = 'user1@yumlog.com'
#     # try:
#     #     cur = connection.cursor()
#     #     sql = "SELECT u.name, u.tags, r.text, r.likes, r2.name \
#     #                 FROM users u JOIN reviews r on u.user_id = r.user_id \
#     #                     JOIN restaurants r2 on r2.restaurant_id = r.restaurant_id \
#     #                 WHERE u.email = '" + email + "';"
#     #     cur.execute(sql)
#     #     rows = cur.fetchall()
#     #     for row in rows:
#     #         username = row[0]
#     #         tags = row[1].split(',')
#     #         review = {
#     #             'text': row[2],
#     #             'likes': row[3],
#     #             'restaurant': row[4],
#     #         }
#     #         reviews.append(review)
            
#     #     cur.close()

#     # except Exception as e:
#     #     print("connection fail: ", e)

#     if request.session['is_logged_in']:
#         email = request.session['user_email']
#         #username = request.session['username']
#         reviews = []
#         try:
#             cur = connection.cursor()
#             sql = "SELECT u.name, u.tags \
#                     FROM users u \
#                     WHERE u.email = '" + email + "';"
#             cur.execute(sql)
#             row = cur.fetchone()
#             username = row[0]
#             tags = row[1].split(',')

#             sql = "SELECT r.text, r.likes, r2.name \
#                     FROM users u JOIN reviews r on u.user_id = r.user_id \
#                         JOIN restaurants r2 on r2.restaurant_id = r.restaurant_id \
#                     WHERE u.email = '" + email + "';"
#             cur.execute(sql)
#             rows = cur.fetchall()
#             for row in rows:
#                 review = {
#                     'text': row[0],
#                     'likes': row[1],
#                     'restaurant': row[2],
#                 }
#                 reviews.append(review)
            
#             cur.close()

#         except Exception as e:
#             print("connection fail: ", e)
    
#     return render(request, 'profile.html', locals())



def public_index(request):
    search_query = request.GET.get('q', '')       # 搜索关键词（可选）
    selected_tags = request.GET.getlist('tags')   # 标签筛选（可选）

    # 查询所有餐厅，并进行搜索过滤（如果有）
    restaurant_qs = restaurants.objects.all()
    if search_query:
        restaurant_qs = restaurant_qs.filter(name__icontains=search_query)
    if selected_tags:
        restaurant_qs = restaurant_qs.filter(category__in=selected_tags)

    # 热门推荐餐厅（评分前 20）
    trending_restaurants = restaurant_qs.order_by('-score')[:20]

    # 点赞数最高的一条评论
    top_review = reviews.objects.select_related('user').order_by('-likes')[:3]


    context = {
        'trending': trending_restaurants,
        'top_review': top_review,
        'search_query': search_query,
        'selected_tags': selected_tags,
    }

    return render(request, 'public_index.html', context)


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
    trending_restaurants = restaurants.objects.order_by('-score')[:20]

    # # 精选评论：点赞数最多
    top_review = reviews.objects.order_by('-likes').first()

    # 个性化推荐逻辑：根据用户 tags 推荐匹配类别的餐厅
    
    recommended_restaurants = []
    print("🚀 已进入 dashboard 视图")

    if request.session.get('is_logged_in'):
        try:
            email = request.session.get('user_email')
            user = users.objects.get(email=email)
            print("✅ 找到当前用户:", user.name)

            if user.tags:
                print("✅ 用户 tags 原始字符串:", user.tags)

                tag_list = [tag.strip().lower() for tag in user.tags.split(',') if tag.strip()]
                print("✅ 清洗后的标签列表:", tag_list)

                # 构造 Q 查询：模糊匹配任意标签
                query = Q()
                for tag in tag_list:
                    print(f"🔍 匹配标签: {tag}")
                    query |= Q(category__icontains=tag)

                matched = restaurants.objects.filter(query).distinct()
                print(f"✅ 匹配到 {matched.count()} 条推荐")

                recommended_restaurants = matched[:5]

        except users.DoesNotExist:
            print("❌ 用户不存在")





    context = {
        'restaurants': restaurant,
        'search_query': search_query,
        'selected_tags': selected_tags,
        'trending': trending_restaurants,
        'top_review': top_review,
        'recommended_restaurants': recommended_restaurants
    }

    return render(request, 'private_index.html', context)



@csrf_exempt
def toggle_like_view(request, review_id):
    if request.method == 'POST':
        try:
            review = reviews.objects.get(pk=review_id)
            liked = request.session.get(f'liked_{review_id}', False)

            if liked:
                review.likes = max(0, review.likes - 1)
                request.session[f'liked_{review_id}'] = False
                liked_now = False
            else:
                review.likes += 1
                request.session[f'liked_{review_id}'] = True
                liked_now = True

            review.save()
            return JsonResponse({'likes': review.likes, 'liked': liked_now})
        except reviews.DoesNotExist:
            return JsonResponse({'error': 'Review not found'}, status=404)





def restaurant_detail_view(request, restaurant_id):
    # 获取餐厅对象
    restaurant = get_object_or_404(restaurants, restaurant_id=restaurant_id)

    # 获取菜单菜品
    menu_dishes = menudishes.objects.filter(restaurant=restaurant)

    # 获取评论（包含用户名）并按点赞排序
    review_list = reviews.objects.filter(restaurant=restaurant).select_related('user').order_by('-likes')
    review_count = review_list.count()

    # 构造菜品与匹配食谱的组合列表
    dish_with_recipe = []
    for dish in menu_dishes:
        matched = match.objects.filter(
            restaurant_id=restaurant.restaurant_id,
            menu_name=dish.menu_name
        ).select_related('recipe').first()

        dish_with_recipe.append({
            'dish': dish,
            'recipe': matched.recipe if matched else None
        })

    # 分割标签
    category_tags = restaurant.category.split(',') if restaurant.category else []

    context = {
        'restaurant': restaurant,
        'dish_with_recipe': dish_with_recipe,
        'review': review_list,
        'review_count': review_count,
        'category_tags': category_tags,
    }

    return render(request, 'restaurant.html', context)

def smart_recs_view(request):
    contexts = []
    page_number_str = request.GET.get('page', '1')
    page_number = int(page_number_str)
    page_range = []
    pre_page, next_page = page_number, page_number
    try:
        cur = connection.cursor()
        cur.execute("SELECT r2.name, m.menu_name, r.title, r.recipe_id, m.restaurant_id \
                    FROM match m JOIN recipes r on r.recipe_id = m.recipe_id \
                        JOIN public.restaurants r2 on m.restaurant_id = r2.restaurant_id \
                    LIMIT 10 OFFSET 10 * (" + page_number_str + " - 1);")
        
        # cur.execute("WITH pagination AS ( \
        #                 SELECT m.menu_name, m.recipe_id, m.restaurant_id \
        #                 FROM match m \
        #                 LIMIT 10 OFFSET 10 * (%s - 1) \
        #             ) \
        #             SELECT r2.name AS restaurant, p.menu_name, r.title AS recipe, r.recipe_id, p.restaurant_id \
        #             FROM pagination p JOIN recipes r on r.recipe_id = p.recipe_id \
        #             JOIN public.restaurants r2 on p.restaurant_id = r2.restaurant_id;", [page_number_str])
        
        rows = cur.fetchall()

        for row in rows:
            context = {
                'restaurant': row[0],
                'menu': row[1],
                'recipe': row[2],
                'recipe_id': row[3],
                'restaurant_id': row[4],
            }
            contexts.append(context)

        cur.execute("SELECT COUNT(*) \
                    FROM match m ;")
        row = cur.fetchone()
        max_page_num = int(int(row[0])/10) + 1
        for i in range(-2, 3):
            if (page_number + i) > 0 and (page_number + i) <= max_page_num:
                page_range.append(page_number + i)
        if (page_number - 1) > 0:
            pre_page = page_number - 1
        if (page_number + 1) < max_page_num:
            next_page = page_number + 1

        cur.close()

    except Exception as e:
        print("connection fail: ", e)

    # paginator = Paginator(contexts, 8)
    # page_obj = paginator.get_page(page_number)

    return render(request, 'smart_recs.html', locals())



    # 社区页视图（Community Feed + Poll）
def community_view(request):
    # 获取最新的 10 条评论作为社区动态
    latest_reviews = reviews.objects.select_related('user', 'restaurant').order_by('-date').values(
    'user__name', 'restaurant__name', 'text')[:5]
    # latest_reviews = reviews.objects.order_by('-date').values_list('text', flat=True)[:5]



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




def restaurant_list_view(request):
    queryset = restaurants.objects.annotate(review_count=Count('reviews'))

    price_range = request.GET.get('price', '').strip()
    category = request.GET.get('category', '').strip()
    score_filter = request.GET.get('score', '').strip()
    search_query = request.GET.get('q', '').strip()  # 🔍 新增搜索关键词

    # ➤ 筛选价格
    if price_range:
        queryset = queryset.filter(price_range=price_range)

    # ➤ 筛选分类
    if category:
        queryset = queryset.filter(category__icontains=category)

    # ➤ 筛选评分
    if score_filter:
        try:
            score = float(score_filter)
            if score >= 4.5:
                queryset = queryset.filter(score__gte=4.5)
            elif score >= 4.0:
                queryset = queryset.filter(score__gte=4.0, score__lt=4.5)
            elif score >= 3.5:
                queryset = queryset.filter(score__gte=3.5, score__lt=4.0)
            elif score >= 3.0:
                queryset = queryset.filter(score__gte=3.0, score__lt=3.5)
            else:
                queryset = queryset.filter(score__lt=3.0)
        except ValueError:
            pass


    # ➤ 搜索关键词匹配（名称 / 地址 / 类别）
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    # ➤ 分页
    paginator = Paginator(queryset, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ➤ 传入模板参数
    context = {
        'restaurants': page_obj.object_list,
        'page_obj': page_obj,
        'selected_price': price_range,
        'selected_category': category,
        'selected_score': score_filter,
        'search_query': search_query,  # ✅ 回传搜索栏值
    }

    return render(request, 'discovery.html', context)


def recipe_detail_view(request):
    # # 获取当前 Recipe 对象
    # recipe = get_object_or_404(recipes, recipe_id=recipe_id)

    # # 获取其它推荐 Recipe（Matched Recipes）
    # matched_recipes = recipes.objects.exclude(recipe_id=recipe_id)[:3]  # 简单逻辑：展示除本身以外的前 3 条，可替换为 NLP 结果

    # # 获取当前 Recipe 匹配到的所有 MenuDish（即：在哪些餐厅有类似的菜）
    # matched_menu_dishes = match.objects.filter(recipe=recipe)

    # # 获取菜品所属餐厅信息
    # similar_restaurants = [match.menudish.restaurant for match in matched_menu_dishes]

    # context = {
    #     'recipe': recipe,                         # 当前菜谱对象
    #     'matched_recipes': matched_recipes,       # 相关推荐菜谱
    #     'similar_restaurants': similar_restaurants  # 相似餐厅（从匹配菜品中提取）
    # }

    # return render(request, 'recipe_detail.html', context)
    recipe_id = request.GET.get('recipe_id')
    try:
        cur = connection.cursor()
        sql = "SELECT title, ingredient, directions, ner \
                FROM recipes \
                WHERE recipe_id = " + recipe_id + ";"
        cur.execute(sql)
        row = cur.fetchone()
        # recipe['recipe'] = row[0]
        recipe = row[0]
        ingredients = clean_string(row[1])
        directions = clean_string(row[2])
        ner = row[3].strip("[]").replace("'", '')
        # recipe['ingredients'] = ingredients
        # recipe['directions'] = directions
        print(row[2])
        cur.close()

    except Exception as e:
        print("connection fail: ", e)

    return render(request, 'recipe.html', locals())

def clean_string(input):
    cleaned = []
    texts = input.strip("[]").split("', ")
    for text in texts:
        text = text.strip("'")
        pattern = r'^[0-9]+\.'
        clean_text = re.sub(pattern, '', text).strip()
        if clean_text != '':
            cleaned.append(clean_text)

    return cleaned




def google_transfer_view(request):
    return render(request, 'signInTransfer.html')

def form_invalid(self, form):
    print("Form errors:", form.errors)
    return super().form_invalid(form)


import logging
from allauth.socialaccount.views import SignupView
from django.urls import reverse

logger = logging.getLogger(__name__)


def google_transfer_view(request):
    # 获取 Google 登录后的用户邮箱
    email = request.user.email

    # ✅ 若数据库中没有该用户，就创建一条记录（用于配合自定义 users 表）
    if not users.objects.filter(email=email).exists():
        uid = f'u{users.objects.count() + 1:03}'  # 生成唯一 user_id
        users.objects.create(
            user_id=uid,
            email=email,
            name='',            # ✅ 初始为空
            password='',        # ✅ Google 登录不需要密码
            tags='',            # ✅ 不默认 American，让用户自己选
            profile='',
            city='',
            state=''
        )
        print(f"[INFO] Created users entry for Google user: {email}")

    # ✅ 登录状态写入 session
    request.session['is_logged_in'] = True
    request.session['user_email'] = email

    return redirect('profile')  # 跳转到 profile 页面让用户补充 tags 和 name


class CustomSocialSignupView(SignupView):
    def dispatch(self, request, *args, **kwargs):
        logger.info(f"CustomSocialSignupView dispatch, path={request.path}")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        logger.info("Redirecting to private_index")
        return reverse('private_index')

    def form_invalid(self, form):
        # Log validation errors when the form is invalid
        logger.error(f"Signup form errors: {form.errors.as_json()}")
        return super().form_invalid(form)

    def form_valid(self, form):
        # Log a message when the form is successfully validated
        logger.info("Signup form valid, proceeding to redirect")
        return super().form_valid(form)

