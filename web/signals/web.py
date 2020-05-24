from django.db.models.signals import post_save
from django.dispatch import receiver
from .. import models
from django.utils.crypto import get_random_string


@receiver(post_save, sender=models.Survey)
def create_unique_code(**kwargs):
    created = kwargs.get("created", False)
    if not created:  # 已经创建过了
        return
    instance = kwargs.get("instance")
    count = instance.count
    codes = []

    while count:      # 批量生成唯一码
        code = get_random_string(8)
        if models.SurveyCode.objects.filter(unique_code=code).exists():  # 是否存在过了
            continue
        codes.append(models.SurveyCode(unique_code=code, survey=instance))
        count -= 1

    models.SurveyCode.objects.bulk_create(codes)
