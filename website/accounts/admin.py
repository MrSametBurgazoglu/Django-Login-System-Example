from django.contrib import admin
from accounts.models import DayLoginCompleteTime

# Register your models here.

class AuthorAdmin(admin.ModelAdmin):
    pass

admin.site.register(DayLoginCompleteTime, AuthorAdmin)