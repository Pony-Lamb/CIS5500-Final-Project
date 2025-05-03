from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)  # 昵称
    email = models.EmailField(unique=True)  # 登录唯一凭证
    password = models.CharField(max_length=128)  # 存储哈希值
    profile = models.TextField(blank=True)
    tags = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Restaurant(models.Model):
    restaurant_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price_range = models.CharField(max_length=10)
    score = models.FloatField(default=0.0)
    address = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=10)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name


class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    likes = models.IntegerField(default=0)
    stars = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.restaurant.name}"


class MenuDish(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    restaurant = models.OneToOneField(Restaurant, on_delete=models.CASCADE, related_name='menu')

    def __str__(self):
        return self.name


class Recipe(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    ingredient = models.TextField()
    directions = models.TextField()
    ner = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class Match(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='matched_dishes')
    menudish = models.ForeignKey(MenuDish, on_delete=models.CASCADE, related_name='matched_recipes')

    def __str__(self):
        return f"{self.recipe.title} ↔ {self.menudish.name}"
