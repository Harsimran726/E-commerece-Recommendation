from django.db import models

# Create your models here.

class Product(models.Model):
    p_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    price = models.FloatField()
    stock = models.IntegerField()
    image_url = models.CharField(max_length=2083)
    category = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    rating = models.IntegerField()
    like = models.IntegerField()
    class Meta:
        ordering = ['-like']
        ordering = ['-rating']
    def __str__(self):
        return f"{self.p_id} - {self.name} -{self.image_url} "

class user_activity(models.Model):
    session_id = models.IntegerField()
    
    LIKE = 'LIKE'
    VIEW = 'VIEW'
    TIME_SPENT = 'TIME_SPENT'
    ADD_TO_BAG = 'ADD_TO_BAG'
    ACTION_CHOICES = [
        (LIKE, 'LIKE'),
        (VIEW, 'VIEW'),
        (TIME_SPENT, 'TIME_SPENT'),
        (ADD_TO_BAG,'ADD_TO_BAG'),
    ]
    action = models.CharField(
        max_length=255, choices=ACTION_CHOICES, default=VIEW,
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    timespent = models.IntegerField(null=True,blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        return f"{self.action} - {self.product.name}"

class bag(models.Model):
    session_id = models.IntegerField()
    size = models.CharField(max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-timestamp']
    def __str__(self):
        return f"{self.product.name} - {self.session_id}"

