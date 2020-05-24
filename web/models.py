from django.db import models
from django.utils.crypto import get_random_string


# Create your models here.


class ClassList(models.Model):
    """
    班级表
    """
    name = models.CharField(max_length=32)


class SurveyCode(models.Model):
    """
    唯一码表，针对某一次问卷调查
    """
    unique_code = models.CharField(max_length=10, unique=True)
    survey = models.ForeignKey("Survey", on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False, verbose_name="是否使用")
    date = models.DateTimeField(auto_now_add=True)


class SurveyTemplate(models.Model):
    """
    问卷模板表
    """
    name = models.CharField(max_length=64, help_text="模板名称(哪个人员的)")
    questions = models.ManyToManyField("SurveyQuestion")
    date = models.DateTimeField(auto_now_add=True)


class SurveyQuestion(models.Model):
    """
    问卷问题表
    """
    survey_type_choices = (
        ("choice", "单选"),
        ("suggest", "建议")
    )
    survey_type = models.CharField(max_length=32, choices=survey_type_choices, verbose_name="问题类型")
    title = models.CharField(max_length=64, verbose_name="问题标题")
    date = models.DateTimeField(auto_now_add=True)


class SurveyChoice(models.Model):
    """
    问卷选项表
    """
    score = models.PositiveSmallIntegerField()
    # related_name加上，方法反向查询
    question = models.ForeignKey("SurveyQuestion", on_delete=models.CASCADE, related_name="choices", verbose_name="关联问题")
    title = models.CharField(max_length=32)
    date = models.DateTimeField(auto_now_add=True)


class SurveyRecord(models.Model):
    """
    问卷记录表
    """
    question = models.ForeignKey("SurveyQuestion", null=True, on_delete=models.CASCADE,verbose_name="哪一个问题")
    survey_template = models.ForeignKey("SurveyTemplate", null=True, verbose_name="哪一个角色的", on_delete=models.CASCADE)
    survey_code = models.ForeignKey("SurveyCode", on_delete=models.CASCADE)
    survey = models.ForeignKey("Survey", on_delete=models.CASCADE, verbose_name="那一次问卷调查")
    choice = models.ForeignKey("SurveyChoice", on_delete=models.CASCADE, null=True, blank=True, verbose_name="问题的选项")
    score = models.PositiveSmallIntegerField(verbose_name="分数", null=True, blank=True)
    content = models.CharField(max_length=1024, verbose_name="建议", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)


class Survey(models.Model):
    """
    问卷调查表
    """
    name = models.CharField(max_length=128, verbose_name="问卷名称")
    grade = models.ForeignKey("ClassList", on_delete=models.CASCADE, verbose_name="哪一个班级的")
    times = models.PositiveSmallIntegerField(verbose_name="第几次问卷调查")
    survey_templates = models.ManyToManyField("SurveyTemplate", verbose_name="针对哪几个角色的问卷调查",blank=True)
    count = models.PositiveSmallIntegerField(verbose_name="生成多少唯一码")
    date = models.DateTimeField(auto_now_add=True)
    created = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # 创建问卷调查表时候创建唯一码
        super().save(*args, **kwargs)
        codes = []
        count = self.count
        while count:
            code = get_random_string(8)
            if SurveyCode.objects.filter(unique_code=code).exists():  # 已经存在了
                continue
            codes.append(SurveyCode(unique_code=code, survey=self))
            count -= 1
        SurveyCode.objects.bulk_create(codes)

