from django.db import models

class users(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)  # 昵称
    email = models.EmailField(unique=True)  # 登录唯一凭证
    password = models.CharField(max_length=128)  # 存储哈希值
    profile = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class restaurants(models.Model):
    restaurant_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    zip_code = models.CharField(max_length=20)
    lat = models.FloatField()
    lng = models.FloatField()
    score = models.FloatField()
    category = models.TextField()
    price_range = models.CharField(max_length=3)

    class Meta:
        db_table = 'restaurants'
       

class reviews(models.Model):
    review_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(users, on_delete=models.CASCADE, related_name='reviews')
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    likes = models.IntegerField(default=0)
    stars = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.restaurant.name}"  # ✅ 修改了这里

    class Meta:
        db_table = 'reviews'   # ✅ 改成你数据库真实的表名
        


class MenuDish(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    restaurant = models.OneToOneField(restaurants, on_delete=models.CASCADE, related_name='menu')

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
