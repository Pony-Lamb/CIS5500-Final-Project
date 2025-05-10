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
                # ✅ set session to mark the user as logged in
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
        tags_str = request.POST.get('tags', '')  # get tags from frontend

        if users.objects.filter(name=username).exists():
            return render(request, 'signup.html', {'errors': {'username': ['Username already exists']}})
        if users.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'errors': {'email': ['Email already exists']}})

        tags_list = tags_str.split(',') if tags_str else []
        tags_final = ','.join([tag.strip() for tag in tags_list])  # remove spaces

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

# log out

def logout_view(request):
    request.session.flush()  # clean all session values
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

        # get username and tags
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

        # ✅ get comments
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
            connection.commit()
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

            # manually generate unique review_id
            cur = connection.cursor()
            cur.execute("SELECT MAX(review_id) FROM reviews;")
            max_id = cur.fetchone()[0] or 0
            next_id = max_id + 1
            cur.close()

            # insert review
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
            print("inserting review failed: ", e)

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
            print("deletion failed: ", e)

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
    search_query = request.GET.get('q', '')       # key words of searching
    selected_tags = request.GET.getlist('tags')   # tags

    # search all restaurants and apply filters
    restaurant_qs = restaurants.objects.all()
    if search_query:
        restaurant_qs = restaurant_qs.filter(name__icontains=search_query)
    if selected_tags:
        restaurant_qs = restaurant_qs.filter(category__in=selected_tags)

    # trending restaurants
    trending_restaurants = restaurant_qs.order_by('-score')[:20]

    # top review with the most likes
    top_review = reviews.objects.select_related('user').order_by('-likes')[:3]


    context = {
        'trending': trending_restaurants,
        'top_review': top_review,
        'search_query': search_query,
        'selected_tags': selected_tags,
    }

    return render(request, 'public_index.html', context)



def home_view(request):
    search_query = request.GET.get('q', '')
    selected_tags = request.GET.getlist('tags')

    restaurant = restaurants.objects.all()

    if search_query:
        restaurant = restaurant.filter(name__icontains=search_query)

    if selected_tags:
        restaurant = restaurant.filter(category__in=selected_tags)

    trending_restaurants = restaurants.objects.order_by('-score')[:20]

    top_review = reviews.objects.order_by('-likes').first()
    
    recommended_restaurants = []
    print("🚀 dashboard")

    if request.session.get('is_logged_in'):
        try:
            email = request.session.get('user_email')
            user = users.objects.get(email=email)
            print("✅ find current user:", user.name)

            if user.tags:
                print("✅ tags string: ", user.tags)

                tag_list = [tag.strip().lower() for tag in user.tags.split(',') if tag.strip()]
                print("✅ tags list: ", tag_list)

                # Q search
                query = Q()
                for tag in tag_list:
                    print(f"🔍 matched tags: {tag}")
                    query |= Q(category__icontains=tag)

                matched = restaurants.objects.filter(query).distinct()
                print(f"✅ matched with {matched.count()} recommendations")

                recommended_restaurants = matched[:5]

        except users.DoesNotExist:
            print("❌ user does not exist")





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
    restaurant = get_object_or_404(restaurants, restaurant_id=restaurant_id)

    menu_dishes = menudishes.objects.filter(restaurant=restaurant)

    # get reviews and ordered by likes
    review_list = reviews.objects.filter(restaurant=restaurant).select_related('user').order_by('-likes')
    review_count = review_list.count()

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
        # cur.execute("SELECT r2.name, m.menu_name, r.title, r.recipe_id, m.restaurant_id \
        #             FROM match m JOIN recipes r on r.recipe_id = m.recipe_id \
        #                 JOIN public.restaurants r2 on m.restaurant_id = r2.restaurant_id \
        #             LIMIT 10 OFFSET 10 * (" + page_number_str + " - 1);")
        
        cur.execute("WITH pagination AS ( \
                        SELECT m.menu_name, m.recipe_id, m.restaurant_id \
                        FROM match m \
                        LIMIT 10 OFFSET 10 * (%s - 1) \
                    ) \
                    SELECT r2.name AS restaurant, p.menu_name, r.title AS recipe, r.recipe_id, p.restaurant_id \
                    FROM pagination p JOIN recipes r on r.recipe_id = p.recipe_id \
                    JOIN public.restaurants r2 on p.restaurant_id = r2.restaurant_id;", [page_number_str])
        
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



def community_view(request):
    # latest 10 reviews
    latest_reviews = reviews.objects.select_related('user', 'restaurant').order_by('-date').values(
    'user__name', 'restaurant__name', 'text')[:5]
    # latest_reviews = reviews.objects.order_by('-date').values_list('text', flat=True)[:5]



    # simulate poll
    poll_question = "What's the best sushi spot in NYC?"
    poll_options = ["Sushi Nakazawa", "Sushi Yasuda", "Sugarfish"]

    # topics
    explore_topics = ["Ramen Spots", "Cheap Eats", "Top Rated"]

    context = {
        'reviews': latest_reviews,
        'poll_question': poll_question,
        'poll_options': poll_options,
        'topics': explore_topics
    }
    return render(request, 'community.html', context)


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
    search_query = request.GET.get('q', '').strip()

    # price filter
    if price_range:
        queryset = queryset.filter(price_range=price_range)

    # category filter
    if category:
        queryset = queryset.filter(category__icontains=category)

    # score filter
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


    # key word search
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    # pagination
    paginator = Paginator(queryset, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'restaurants': page_obj.object_list,
        'page_obj': page_obj,
        'selected_price': price_range,
        'selected_category': category,
        'selected_score': score_filter,
        'search_query': search_query,  # ✅ search input
    }

    return render(request, 'discovery.html', context)


def recipe_detail_view(request):
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
    # Google email
    email = request.user.email

    # ✅ create a user
    if not users.objects.filter(email=email).exists():
        uid = f'u{users.objects.count() + 1:03}'  # unique user_id
        users.objects.create(
            user_id=uid,
            email=email,
            name='',
            password='',
            tags='',
            profile='',
            city='',
            state=''
        )
        print(f"[INFO] Created users entry for Google user: {email}")

    request.session['is_logged_in'] = True
    request.session['user_email'] = email

    return redirect('profile')

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

