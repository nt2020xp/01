# -*- coding: utf-8 -*-
import base64
import sys
import json
import time
import requests
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "台湾4g备用(py10175)"

    def init(self, extend):
        self.proxy = None
        self.is_proxy = False
        self.subscription_url = "http://141.11.87.241:20013/?type=m3u"
        # 控制刷新间隔：避免频繁请求（默认5秒重试一次）
        self.refresh_interval = 5
        
        if extend:
            try:
                self.extendDict = json.loads(extend)
                self.proxy = self.extendDict.get("proxy")
                self.is_proxy = self.proxy is not None
                # 支持从extend动态调整刷新间隔（单位：秒）
                if self.extendDict.get("refresh_interval"):
                    self.refresh_interval = int(self.extendDict.get("refresh_interval"))
                    print(f"已加载自定义刷新间隔：{self.refresh_interval}秒")
                # 支持动态覆盖订阅链接
                if self.extendDict.get("subscription_url"):
                    self.subscription_url = self.extendDict.get("subscription_url")
                    print(f"已加载自定义订阅链接：{self.subscription_url}")
                if self.is_proxy:
                    print(f"已启用代理：{list(self.proxy.keys())}")
            except Exception as e:
                print(f"extend参数解析错误：{str(e)}，使用默认配置")

    def isVideoFormat(self, url):
        return True
    def manualVideoCheck(self):
        return True

    def liveContent(self, url):
        # 核心逻辑：订阅失败不返回应急频道，循环刷新重试
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "close",  # 禁用长连接，适配不稳定服务器
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        retry_count = 1  # 计数，便于日志跟踪重试次数

        while True:  # 无限循环，直到请求成功
            try:
                print(f"【订阅刷新】第{retry_count}次尝试，订阅链接：{self.subscription_url}")
                # 细分超时：5秒连接超时，20秒读取超时
                response = requests.get(
                    self.subscription_url,
                    headers=headers,
                    proxies=self.proxy if self.is_proxy else None,
                    timeout=(5, 20),
                    verify=False,
                    allow_redirects=True
                )

                print(f"【响应状态】第{retry_count}次：状态码{response.status_code}")
                response.raise_for_status()  # 非200状态码抛异常

                # 请求成功：返回订阅的频道列表
                m3u_content = response.text.strip()
                channel_count = m3u_content.count("#EXTINF")
                print(f"【刷新成功】第{retry_count}次尝试成功，获取{channel_count}个频道")
                return m3u_content

            except Exception as e:
                # 订阅失败：打印错误，等待指定间隔后重新刷新
                error_msg = f"【刷新失败】第{retry_count}次：{type(e).__name__} - {str(e)}"
                print(f"{error_msg}，{self.refresh_interval}秒后重新尝试")
                retry_count += 1
                time.sleep(self.refresh_interval)  # 等待后继续循环重试

    # 影视壳必需空接口（保持不变）
    def homeContent(self, filter):
        return {"class": [], "list": []}
    def homeVideoContent(self):
        return {"list": []}
    def categoryContent(self, cid, page, filter, ext):
        return {"list": [], "page": page, "pagecount": 1, "total": 0}
    def detailContent(self, did):
        return {}
    def searchContent(self, key, quick, page='1'):
        return {"list": [], "page": page, "pagecount": 1, "total": 0}
    def searchContentPage(self, keywords, quick, page):
        return self.searchContent(keywords, quick, page)

    def playerContent(self, flag, pid, vipFlags):
        return {"parse": 0, "playUrl": "", "header": {}}

    def localProxy(self, params):
        if params.get('type') in ["mpd", "ts"] and 'url' in params:
            try:
                url = self.b64decode(params['url'])
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', "Connection": "close"}
                resp = requests.get(
                    url,
                    headers=headers,
                    proxies=self.proxy if self.is_proxy else None,
                    stream=True,
                    verify=False,
                    timeout=(5, 30)
                )
                return [200, resp.headers.get('Content-Type', 'application/octet-stream'), resp.content, dict(resp.headers)]
            except Exception as e:
                print(f"代理转发失败：{str(e)}")
        return [302, "text/plain", None, {'Location': 'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4'}]

    def b64encode(self, data):
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')
    def b64decode(self, data):
        return base64.b64decode(data.encode('utf-8')).decode('utf-8')

# 本地测试逻辑（运行脚本验证循环刷新效果）
if __name__ == '__main__':
    print("=== 台湾4g备用爬虫 本地测试（循环刷新模式）===")
    spider = Spider()
    # 测试时可通过extend调整刷新间隔（示例：3秒刷新一次）
    # test_extend = '{"refresh_interval":3, "proxy":{"http":"http://127.0.0.1:7890","https":"https://127.0.0.1:7890"}}'
    test_extend = "{}"
    spider.init(test_extend)
    
    try:
        # 调用liveContent，会一直循环直到订阅成功
        content = spider.liveContent("test")
        print(f"\n=== 测试成功 ===")
        print(f"频道数量：{content.count('#EXTINF')} 个")
        print(f"前5行内容预览：")
        for i, line in enumerate(content.split('\n')[:5], 1):
            print(f"  {i}. {line}")
    except KeyboardInterrupt:
        print(f"\n=== 测试中断（用户手动停止）===")
    except Exception as e:
        print(f"\n测试异常：{str(e)}")
