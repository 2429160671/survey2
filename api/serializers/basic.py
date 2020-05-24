from rest_framework import serializers
from django.template import loader
from web import models
from django.urls import reverse
from django.db import transaction


# 序列化器，从此处获取数据，需要对数据进行加工则在此处进行
class SurveySerializer(serializers.ModelSerializer):

    grade = serializers.CharField(source="grade.name")
    valid_count = serializers.SerializerMethodField()     # 有效数量
    handle_link = serializers.SerializerMethodField()     # 调查链接
    handle = serializers.SerializerMethodField()          # 操作
    date = serializers.DateTimeField(format('%Y-%m-%d %H:%M:%S'))

    class Meta:
        model = models.Survey
        fields = (
            "grade",
            "name",
            "valid_count",
            "times",
            "date",
            "handle_link",
            "handle"
        )

    # 方法加工数据，然后返回
    def get_valid_count(self, instance):
        # 有效填写人次
        return models.SurveyCode.objects.filter(survey=instance, is_used=True).count()

    def get_handle_link(self, instance):
        # 填写链接
        request = self.context.get("request")
        # 拼接填写链接，使用reverse反射来找到对应的链接，之后只需要修改urls.py
        link = "{}://{}{}".format(
            request.scheme,
            request.get_host(),
            reverse('survey_detail', args={instance.pk})
        )
        return "<a href='{}'>{}</a>".format(link, link)

    def get_handle(self, instance):
        return loader.render_to_string(
            "web/components/handle.html",
            context={
                "report_link": f"survey/{instance.pk}/report/",
                "download_link": f"/{instance.pk}/download/"
            }
        )


class SurveyChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.SurveyChoice
        fields = (
            "title",
            "score",
            "id"
        )


class SurveyQuestionSerializer(serializers.ModelSerializer):
    # 添加的选项字段，反向查询
    # choices = serializers.SerializerMethodField()
    # 这种方法也可以，更方便
    # choices = SurveyChoiceSerializer(many=True, source="surveychoice_set.all")
    # 如果在models之中给SurveyChoice.questions加上了related_name，则可以这样进行反向查询,source都不用加了
    # 注意是relate_name和自定义的字段名相同，就不用加source
    choices = SurveyChoiceSerializer(many=True)
    value = serializers.CharField(default="", error_messages={
        'invalid': "类型无效",
        'blank': "输入不能为空",
    })
    error = serializers.CharField(default="", required=False, allow_null=True, allow_blank=True)
    question = serializers.IntegerField(required=True, write_only=True)

    class Meta:
        model = models.SurveyQuestion
        fields = (
            "id",
            "survey_type",
            "title",
            "choices",
            "value",
            "error",
            "question"
        )

    def get_choices(self, instance):
        # return models.SurveyChoice.objects.filter(question=instance.pk).values()
        # 取当前survey的所有choice
        return list(instance.surveychoice_set.values())

    def to_internal_value(self, data):
        data['question'] = self.Meta.model.objects.get(pk=data['id'])
        return data


class SurveyTemplateSerializer(serializers.ModelSerializer):

    # 一对多关系，指定子序列化器
    questions = SurveyQuestionSerializer(many=True)

    class Meta:
        model = models.SurveyTemplate
        fields = (
            "id",
            "name",
            "questions"
        )


class SurveyDetailSerializer(serializers.ModelSerializer):

    # 多对多关系，需要指定子序列化器
    survey_templates = serializers.ListSerializer(child=SurveyTemplateSerializer())

    class Meta:
        model = models.Survey
        fields = (
            "id",
            "name",
            "survey_templates",
        )

    
# 创建的序列化器，创建需要进行数据校验，区分开
class SurveyCreateSerializer(serializers.ModelSerializer):
    # 多对多关系，需要指定子序列化器
    survey_templates = serializers.ListSerializer(child=SurveyTemplateSerializer())
    unique_code = serializers.CharField(allow_blank=False, error_messages={
        "blank": "唯一码不能为空"
    })

    class Meta:
        model = models.Survey
        fields = (
            "survey_templates",
            "unique_code"
        )

    # 局部钩子函数，判断唯一码是否已经使用过了
    def validate_unique_code(self, attrs):
        code = models.SurveyCode.objects.filter(unique_code=attrs).first()
        if not code:
            raise serializers.ValidationError("无效的唯一码")
        code = models.SurveyCode.objects.filter(unique_code=attrs, is_used=False).first()
        if not code:
            raise serializers.ValidationError("唯一码已经被使用")
        return code

    def create(self, validated_data):
        print(validated_data)
        survey_templates = validated_data.get("survey_templates", [])
        unique_code = validated_data['unique_code']
        survey = models.Survey.objects.filter(pk=self.context.get('view').kwargs['pk']).first()
        survey_records = []
        with transaction.atomic():
            try:
                save_id = transaction.savepoint()
                for template in survey_templates:
                    for question in template.get("questions", []):
                        _data = {
                            "question": question.get("question"),
                            "survey_code": unique_code,
                            "survey": survey,
                        }
                        # 单选题
                        if question.get('survey_type') == "choice":
                            # 记录选择的选项
                            # print('----', question.get("value"))
                            choice = models.SurveyChoice.objects.filter(id=question.get("value")).first()
                            _data['choice'] = choice
                            _data['score'] = choice.score
                        else:
                            # 建议类型记录答案
                            _data['content'] = question.get("value")
                        # print('数据:', _data)
                        models.SurveyRecord.objects.create(**_data)
                        survey_records.append(_data)

                unique_code.is_used = True
                unique_code.save()
                transaction.savepoint_commit(save_id)
            except Exception as e:
                print(e)
                transaction.savepoint_rollback(save_id)
        # with transaction.atomic():
        #     try:
        #         # 创建事务保存点
        #         save_id = transaction.savepoint()
        #         unique_code.save(update_fields=("is_used", ))
        #         models.SurveyRecord.objects.bulk_create(survey_records)
        #         # 提交事务
        #         transaction.savepoint_commit(save_id)
        #     except Exception as e:
        #         print(e)
        #         transaction.savepoint_rollback(save_id)    # 出错回滚

        return {}