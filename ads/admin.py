from django.contrib import admin
from .models import Category, Ads, Response


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(Ads)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author', 'category', 'is_published', 'created_at')
    list_filter = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'content')


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id','author','ads','is_accepted','created_at')
    list_filter = ('is_accepted','created_at')
    search_fields = ('author__username','ads__title','text')
    readonly_fields = ('created_at',)