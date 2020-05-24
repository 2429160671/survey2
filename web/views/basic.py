from django.views.generic import TemplateView
from django.conf import settings
from django.http.response import StreamingHttpResponse, JsonResponse
from urllib.request import quote
from .. import models
import os
import xlwt
from django.utils.crypto import get_random_string


class TestView(TemplateView):

    template_name = "web/test.html"


class IndexView(TemplateView):

    template_name = "web/index.html"


class DownloadView(TemplateView):

    # 下载当前问卷调查的唯一码文件
    def get(self, request, *args, **kwargs):
        # 只取出unique_code
        codes = models.SurveyCode.objects.filter(survey=kwargs.get("pk")).values_list("unique_code")
        codes = list(codes)
        survey_name = models.Survey.objects.filter(id=kwargs.get("pk")).values_list("name")[0]
        # 存储到excel
        book = xlwt.Workbook()
        table = book.add_sheet("sheet1")
        table.write(0, 0, "唯一码号")
        # 迭代遍历，节省内存
        for index, code in enumerate(codes, 1):
            table.write(index, 0, code)
        book.save("唯一码.xls")

        # 文件流
        def iter_file(path, size=1024):
            with open(path, 'rb') as f:
                for data in iter(lambda: f.read(size), b""):
                    yield data

        response = StreamingHttpResponse(iter_file(os.path.join(settings.BASE_DIR, "唯一码.xls")))
        # content-type
        response['Content-Type'] = 'application/octet-stream'
        # 内容描述
        response['Content-Disposition'] = 'attachment; {}'.format(
            "filename*={}".format(quote(str(survey_name[0])+"--唯一码.xls"))
        )

        return response


class SurveyDetailView(TemplateView):

    template_name = "web/detail.html"


class SurveyReportView(TemplateView):

        template_name = "web/report.html"


def create_codes(request):
    codes = []
    surveys = models.Survey.objects.all()
    for survey in surveys:
        count = 10
        while count:
            code = get_random_string(10)
            if models.SurveyCode.objects.filter(unique_code=code).exists():  # 已经存在了
                continue
            codes.append(models.SurveyCode(unique_code=code, survey=survey))
            count -= 1
    models.SurveyCode.objects.bulk_create(codes)
    return JsonResponse({"code": 0})