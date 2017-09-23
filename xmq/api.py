# -*- coding: utf-8 -*-
import json
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import url_matches
from selenium.webdriver.support.wait import WebDriverWait

from xmq.settings import CHROME_DRIVER_PATH
from xmq.webdriver.expected_conditions import cookie_is_set, element_is_complete
from xmq.webdriver.support import AutoClosableChrome


class XmqLogin(object):
    """
    小密圈二维码登录插件
    """

    @staticmethod
    def get_access_token(spider):
        """
        登录并获取access_token
        :param spider: 调用的爬虫
        :return: access_token
        """

        with AutoClosableChrome(CHROME_DRIVER_PATH) as driver:
            driver.get(XmqApi.URL_LOGIN)

            # 等待跳转至主页
            WebDriverWait(driver, 60).until(url_matches(r'index/\d+'))
            spider.logger.info('登录成功')

            # 等待access_token加载完毕
            access_token = WebDriverWait(driver, 30).until(cookie_is_set('access_token'))
            access_token = access_token['value']
            spider.logger.info('access_token加载成功: %s' % access_token)

            # 等待头像加载完毕
            # 直接返回的token是不合法的，需要等待浏览器提交某请求使其合法，而该提交先于头像的加载
            avatar_complete = element_is_complete((By.CSS_SELECTOR, 'p.avastar-p img'))
            WebDriverWait(driver, 30).until(avatar_complete)
            spider.logger.info('头像加载成功')

            return access_token


class XmqApi(object):
    """
    小密圈API插件
    """

    URL_API = 'https://api.xiaomiquan.com/v1.7/'
    URL_TOPICS_FORMAT = urljoin(URL_API, 'groups/{group_id}/topics?count=20&end_time={end_time}')

    URL_LOGIN = 'https://wx.xiaomiquan.com/dweb/#/login'
    URL_GROUPS = urljoin(URL_API, 'groups')

    @staticmethod
    def URL_TOPICS(group_id, from_data=None):
        """
        话题数据API

        该API逻辑为，获取截止`end_time`时间最新的`count`条话题，
        并将最后一条话题的`create_time - 1ms`作为下次请求的`end_time`，
        为了避免对毫秒的处理，本项目直接使用`create_time`，并在返回结果中筛去。

        :param group_id: 圈子id
        :param from_data: 上次请求所得的数据
        :return: 本次应请求的URL
        """
        params = {
            'group_id': group_id,
            'end_time': '' if from_data is None else XmqApi.extract_data(from_data)['topics'][-1]['create_time']
        }
        return XmqApi.URL_TOPICS_FORMAT.format(**params)

    @staticmethod
    def extract_data(response):
        return json.loads(response.text).get('resp_data', None)
