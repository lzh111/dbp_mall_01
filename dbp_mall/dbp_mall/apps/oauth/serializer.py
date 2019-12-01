from django_redis import get_redis_connection
from rest_framework import serializers

from .utils import check_save_user_token
from users.models import User
from .models import oAuthQQUser


class QQAuthUserSerializer(serializers.Serializer):
    """openid绑定用户的序列化器"""

    # 需要校验那些字段 'mobile, password  sms_code  access_token'
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')  # 手机号定义字段类型为正则,这样后续就不用再单独校验手机号了
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')



    def validate(self, attrs):
        # 把加密的openid 取出来进行解密
        openid_sign = attrs.pop('access_token')
        openid = check_save_user_token(openid_sign)
        # 如果获取openid 失败
        if not openid:
            raise serializers.ValidationError('access_token无效')
        # 如果获取到openid 把openid 添加到attrs 后续create方法中需要使用
        attrs['openid'] = openid

        # 校验短信验证码
        mobile = attrs.get('mobile')
        # 创建redis连接
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # 向redis存储数据时,都是以字符串的格式存储进行,将来获取出来后,都会变成'bytes'类型: str: bytes hash: {b'key':b''} list:[b'',] set:[b'']
        if not real_sms_code:
            raise serializers.ValidationError('验证码过期')
        # 此处一定要注意从redis中取出来的字符串是bytes类型需要转换成str
        if real_sms_code.decode() != attrs.get('sms_code'):
            raise serializers.ValidationError('验证码有误')

        try:
            # 用手机号去获取user
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果手机好不存在，pass
            pass
        else:
            # 如果通过手机号获取到user，那么说明此用户是已存在用户，就不用创建用户
            password = attrs.get('password')
            # 校验当前获取出的旧user对应前端传入密码是否正确
            if not user.check_password(password):
                raise serializers.ValidationError('密码不正确')
            # 如果user已存在并且密码也正确，将user也添加到attrs中，以便后续绑定需要
            attrs['user'] = user

        return attrs


    def create(self, validated_data):
        """openid和user进行绑定"""
        # 先从validated_data里面获取 有没有user
        user = validated_data.get('user')
        # 如果有，那么就不用在创建user
        # 如果没有，创建一个新的user并保存
        if not user:
            user = User(
                username = validated_data.get('mobile'),
                # password = validated_data.get('password'),
                mobile = validated_data.get('mobile')
            )
            user.set_password(validated_data.get('password'))
            user.save()

        # 创建oAuthQQUser 模型对象， 让openid和user进行绑定
        oAuthQQUser.objects.create(
            user=user,
            openid = validated_data.get('openid')
        )

        return user

