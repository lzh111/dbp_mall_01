from dbp_mall.settings import dev
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
import logging
import json
from itsdangerous import TimedJSONWebSignatureSerializer as TJSSerializer, BadData

from .exceptions import QQAPIException

logger = logging.getLogger('django')

def check_save_user_token(openid_sign):
    """
    对加密后的openid 进行解密
    :param open_sign: 加密后的openid
    :return: 加密成功返回openid 失败返回None
    """

    # 1.创建加载的系列化器对象
    serializer = TJSSerializer(secret_key=dev.SECRET_KEY, expires_in=600)
    # 2.调用loads方法进行对数据加密
    try:
        data = serializer.loads(openid_sign)
    except BadData: # 如果解密失败会抛出BadData的异常
        return None
    else:
        return data.get('openid')

class OAuthQQ(object):
    """
    用户QQ登陆的工具类，
    提供了QQ登录可能使用的方法
    """
    def __init__(self, app_id=None, app_key=None, redirect_url=None, state=None):
        self.app_id = app_id or dev.QQ_APP_ID
        self.app_key = app_key or dev.QQ_APP_KEY
        self.redirect_url = redirect_url or dev.QQ_REDIRECT_URL
        self.state = state or dev.QQ_STATE

    def generate_qq_login_url(self):
        """
        拼接用户QQ登录的链接地址
        :return: 链接地址
        """
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        data = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_uri': self.redirect_url,
            'state': self.state,
            'scope': 'get_user_info'  # 获取用户的qq的openid
        }
        query_string = urlencode(data)  #  response_type=code&client_id=xxxx&redirect_uri=xxxxx&....
        url += query_string
        print(url)

        return url

    def get_access_token(self, code):
        """
        获取qq的access_token
        :param code: 调用的凭据
        :return: access_token
        """
        url = 'https://graph.qq.com/oauth2.0/token?'
        req_data = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_url
        }
        url += urlencode(req_data)

        try:
            # 发送请求
            response = urlopen(url)
            # 读取QQ返回的响应体数据
            # access_token=FE04************************CCE2&expires_in=7776000&refresh_token=88E4************************BE1
            response = response.read().decode()

            # 将返回的数据转换为字典
            resp_dict = parse_qs(response)

            access_token = resp_dict.get("access_token")[0]
        except Exception as e:
            logger.error(e)
            raise QQAPIException('获取access_token异常')

        return access_token

    def get_openid(self, access_token):
        """
        获取用户的openid
        :param access_token: qq提供的access_token
        :return: open_id
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token
        try:
            response = urlopen(url)
            response_data = response.read().decode()
            # 返回的数据 callback( {"client_id":"YOUR_APPID","openid":"YOUR_OPENID"} )\n;
            data = json.loads(response_data[10:-4])
        except Exception:
            data = parse_qs(response_data)
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIException('获取openid异常')

        openid = data.get('openid', None)
        return openid














