from django.contrib import admin
from .models import * 
# Register your models here.
admin.site.register(Product)
admin.site.register(user_activity)

admin.site.register(bag)