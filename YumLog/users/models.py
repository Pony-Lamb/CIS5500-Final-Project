from django.db import models

class users(models.Model):
    user_id = models.CharField(primary_key=True, max_length=50)  
    name = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    tags = models.TextField(blank=True)
    profile = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    email = models.TextField()

    def __str__(self):
        return f"{self.name} ({self.user_id})"

    class Meta:
        db_table = 'users'                      


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
    user = models.ForeignKey(users, on_delete=models.CASCADE, db_column='user_id', to_field='user_id')
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    likes = models.IntegerField(default=0)
    stars = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} - {self.restaurant.name}"  # ✅ 修改了这里

    class Meta:
        db_table = 'reviews'   # ✅ 改成你数据库真实的表名
        managed = False  
        


class menudishes(models.Model):
    restaurant = models.ForeignKey(restaurants, on_delete=models.CASCADE)
    menu_name = models.CharField(max_length=100)
    category = models.TextField(blank=True)
    price = models.FloatField()
    popularity_score = models.FloatField(default=0.0)

    class Meta:
        db_table = 'menudishes'              # ✅ 使用数据库真实表名
        managed = False                      # ✅ 禁止 Django 管理表结构
        unique_together = (('restaurant', 'menu_name'),)



class recipes(models.Model):
    recipe_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    ingredient = models.TextField()
    directions = models.TextField()
    ner = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'recipes'   # ✅ 显式指定真实的数据库表名
        managed = False        


class match(models.Model):
    restaurant_id = models.IntegerField()
    menu_name = models.CharField(max_length=100)
    recipe = models.ForeignKey(recipes, on_delete=models.DO_NOTHING, db_column='recipe_id')

    class Meta:
        db_table = 'match'         

