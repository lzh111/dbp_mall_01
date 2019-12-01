# from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from django_redis import get_redis_connection
from django.http.response import HttpResponse
from rest_framework.generics import GenericAPIView
import random
from rest_framework.response import Response
#
from dbp_mall.libs.captcha.captcha import captcha
from . import constants
from . import serializers
# from dbp_mall.utils.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms_code
# from users.models import User
# Create your views here.


class ImageCodeView(APIView):
    """
    图片验证码
    """
    def get(self, request, image_code_id):

        # 生成验证码图片
        text, image = captcha.generate_captcha()

        # 获取redis的连接对象
        redis_conn = get_redis_connection("verify_codes")
        # 保存到数据库并设置过期时间
        redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        return HttpResponse(image, content_type="image/jpg")
        # content_type  images:下载   image:图片
        # 问题一，为啥还能返回HttpResponse，不是应该返回Response对象么?
        # 首先Response是间接继承HttpResponse的，而视图本身就应该返回的是HttpResponse。在DRF中可以返回Response，主要是因为Response继承了HttpResponse。

        # 问题二，为啥不返回Response？
        # 这是因为Response会将内容交给json渲染器进行数据格式转换，

        # 但是我们这里是要返回一张图片,前端要求的类型是json的那么将图片交给json渲染器是会报错的。

class SMSCodeView(GenericAPIView):
    serializer_class = serializers.ImageCodeCheckSerialzier

    def get(self, request, mobile):
        # 校验图片验证码和s发送短信的频次
        # mobile是被放到了类视图对象属性kwargs中
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)


        # 校验通过
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存验证码及发送记录
        redis_conn = get_redis_connection('verify_codes')
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用redis的pipeline管道一次执行多个命令
        pl = redis_conn.pipeline()
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # # 让管道执行命令
        pl.execute()

        # 发送短信



        #
        # ccp = CCP()
        # time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
        # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)

        # 使用celery发布异步任务
        print(mobile,sms_code)
        send_sms_code.delay(mobile, sms_code)

        # 返回
        return Response({"message":"OK"})


# class SMSCodeByTokenView(APIView):
#     """根据access_token发送短信"""
#     def get(self, request):
#         # 获取并校验 access_token
#         access_token = request.query_params.get('access_token')
#         if not access_token:
#             return Response({"message": "缺少access token"}, status=status.HTTP_400_BAD_REQUEST)
#
#         # 从access_token中取出手机号
#         mobile = User.check_send_sms_code_token(access_token)
#         if mobile is None:
#             return Response({"message": "无效的access token"}, status=status.HTTP_400_BAD_REQUEST)
#
#
#         # 判断手机号发送的次数
#         redis_conn = get_redis_connection('verify_codes')
#         send_flag = redis_conn.get('send_flag_%s' % mobile)
#         if send_flag:
#             return Response({"message": "发送短信次数过于频"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
#
#         # 生成短信验证码
#         # 发送短信验证码
#         sms_code = '%06d' % random.randint(0, 999999)
#
#         # 保存验证码及发送记录
#         # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#
#         # 使用redis的pipeline管道一次执行多个命令
#         pl = redis_conn.pipeline()
#         pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#         # 让管道执行命令
#         pl.execute()
#
#         # 发送短信
#         # ccp = CCP()
#         # time = str(constants.SMS_CODE_REDIS_EXPIRES / 60)
#         # ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
#         # 使用celery发布异步任务
#         send_sms_code.delay(mobile, sms_code)
#
#         # 返回
#         return Response({'message': 'OK'})
#
#
#
#
#
#








