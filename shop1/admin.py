from django.contrib import admin
# Category را به این خط اضافه کنید
from .models import Post, Comment, Category

# این بخش جدید را اضافه کنید
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)} # این خط به صورت خودکار اسلاگ را پر می‌کند

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'publish', 'create', 'update')
    list_filter = ('status', 'create', 'publish')
    search_fields = ('title', 'desc')
    date_hierarchy = 'publish'
    ordering = ('status', 'publish')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'create', 'active')
    list_filter = ('active', 'create', 'update')
    search_fields = ('body', 'user__username')