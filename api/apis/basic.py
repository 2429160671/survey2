from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework import filters
from web import models
from ..serializers import basic
from django.http import JsonResponse
from rest_framework import pagination
from django.conf import settings
from rest_framework.response import Response
import math
from django.db.models import Sum


class MYFilter(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        """
        :param request:     rest_framwork  request
        :param queryset:    结果集
        :param view:         视图
        :return:
        """
        pass


# 获取主页数据
class SurveyApi(ListAPIView):
    """
    model,序列化器
    """
    # 表格头
    table_column = [{
                "prop": "name",
                "label": "问卷名称"
            }, {
                "prop": "grade",
                "label": "班级"
            }, {
                "prop": "valid_count",
                "label": "填写人次"
            },
            {
                "prop": "handle_link",
                "label": "填写链接"
            },
            {"prop": "date", "label": "日期"},
            {
                 "prop": "handle",
                 "label": "操作"
            }]
    queryset = models.Survey.objects.all()
    serializer_class = basic.SurveySerializer

    # 过滤器
    filter_backends = (filters.SearchFilter, filters.OrderingFilter,)
    # 搜索字段
    search_fields = ("name", )
    # 排序字段
    ordering_fields = '__all__'

    # 指定分页器，可以自定义，指定自己的类也可以，不过要继承对应的分页器类
    pagination_class = pagination.LimitOffsetPagination

    # 重写list方法，返回table_column，默认的只是返回data
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # 实现分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return JsonResponse({
                "code": 0,
                "data": {
                    "table_column": self.table_column,
                    'table_data': serializer.data,
                    "count": math.ceil(len(queryset) / settings.REST_FRAMEWORK['PAGE_SIZE']),
                }
            })

        serializer = self.get_serializer(queryset, many=True)
        return JsonResponse({
            "code": 0,
            "data": {
                "table_column": self.table_column,
                'table_data': serializer.data
            }
        })


# 单条数据 RetrieveAPIView
class SurveyDetailApi(RetrieveAPIView, CreateAPIView):
    queryset = models.Survey.objects.all()
    serializer_class = basic.SurveyDetailSerializer

    # 根据post,get设置不同的序列化器
    def get_serializer_class(self):
        if self.request.method == "GET":
            return basic.SurveyDetailSerializer
        else:
            return basic.SurveyCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.save()
            return Response({
                "code": 0,
                "data": data
            })
        else:
            return Response({
                "code": 1,
                "errors": serializer.errors
            })

    # # 改写retrieve方法，返回单条数据
    # def retrieve(self, request, *args, **kwargs):
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     return Response(serializer.data)


# 问卷报告
class SurveysReportApi(RetrieveAPIView):

    def retrieve(self, request, *args, **kwargs):
        # 查询当前调查问卷下每一个问题的总分值
        result = models.SurveyRecord.objects.filter(
            question__survey_type="choice", survey=kwargs.get("pk"))\
            .values("question__title") \
            .annotate(Sum("score"))
        return Response({
            "code": 0,
            "data": list(result)
        })


