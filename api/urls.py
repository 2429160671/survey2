from django.urls import path, include, re_path
from .apis import basic


urlpatterns = [
    path("surveys/", basic.SurveyApi.as_view()),
    path(r"surveys/<int:pk>/", basic.SurveyDetailApi.as_view()),
    path("surveys/<int:pk>/report/", basic.SurveysReportApi.as_view())
]
