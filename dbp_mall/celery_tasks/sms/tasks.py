from .yuntongxun.sms import CCP
from . import constants
from celery_tasks.main import celery_app
import logging
logger = logging.getLogger('django')

@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信任务
    :param mobile: 手机号
    :param sms_code: 验证码
    :return: None
    """
    # 发送短信
    ccp = CCP()
    time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
    print(mobile)
    # 发送模板短信
    # @param to  必选参数     短信接收彿手机号码集合,用英文逗号分开
    # @param datas 可选参数    内容数据
    # @param tempId 必选参数    模板Id
    ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)
