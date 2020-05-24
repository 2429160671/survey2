from django.contrib import admin
from . import models
# Register your models here.


admin.site.register(models.Survey)
admin.site.register(models.ClassList)
admin.site.register(models.SurveyCode)
admin.site.register(models.SurveyTemplate)
admin.site.register(models.SurveyChoice)
admin.site.register(models.SurveyQuestion)
admin.site.register(models.SurveyRecord)
