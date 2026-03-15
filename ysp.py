
import base64
import sys
import os
import time
import json
import requests
import uuid
import hashlib
import logging
import random
from urllib.parse import urlencode, urlparse
from collections import OrderedDict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
sys.path.append('..')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("央视频")

# ================================================================
#  RSA 工具（纯Python实现，无外部加密库依赖）
# ================================================================

_PUB_KEY_B64 = (
    'MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC/ZeLwTPPLSU7QGwv6tVgdawz9'
    'n7S2CxboIEVQlQ1USAHvBRlWBsU2l7+HuUVMJ5blqGc/5y3AoaUzPGoXPfIm0GnB'
    'dFL+iLeRDwOS1KgcQ0fIquvr/2Xzj3fVA1o4Y81wJK5BP8bDTBFYMVOlOoCc1ZzWw'
    'dZBYpb4FNxt//5dAwIDAQAB'
)
_APP_ID = '5f39826474a524f95d5f436eacfacfb67457c4a7'
_APP_VERSION = '1.3.7'


def _parse_der_public_key(der_bytes):
    """解析DER编码的RSA公钥，返回(n, e)"""
    pos = [0]

    def rb():
        b = der_bytes[pos[0]]; pos[0] += 1; return b

    def read_len():
        b = rb()
        if b & 0x80 == 0:
            return b
        cnt = b & 0x7f
        length = 0
        for _ in range(cnt):
            length = (length << 8) | rb()
        return length

    def read_int():
        if rb() != 0x02:
            raise ValueError("非INTEGER标签")
        ln = read_len()
        val = int.from_bytes(der_bytes[pos[0]:pos[0] + ln], 'big')
        pos[0] += ln
        return val

    # 外层SEQUENCE
    rb(); read_len()
    # 算法SEQUENCE
    rb(); algo_len = read_len(); pos[0] += algo_len
    # BIT STRING
    rb(); read_len(); rb()
    # 内层SEQUENCE
    rb(); read_len()
    return read_int(), read_int()


# 预加载公钥
try:
    _RSA_N, _RSA_E = _parse_der_public_key(base64.b64decode(_PUB_KEY_B64))
    _RSA_KEY_SIZE = (_RSA_N.bit_length() + 7) // 8
except Exception as _e:
    logger.error(f"RSA公钥加载失败: {_e}")
    _RSA_N = _RSA_E = _RSA_KEY_SIZE = None


def rsa_public_encrypt(data):
    """RSA公钥加密(PKCS1v15 Type2)，对应PHP的openssl_public_encrypt"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    pad_len = _RSA_KEY_SIZE - len(data) - 3
    if pad_len < 8:
        raise ValueError("数据过长")
    pad = bytearray()
    while len(pad) < pad_len:
        b = os.urandom(1)[0]
        if b != 0:
            pad.append(b)
    m = int.from_bytes(b'\x00\x02' + bytes(pad) + b'\x00' + data, 'big')
    c = pow(m, _RSA_E, _RSA_N)
    return base64.b64encode(c.to_bytes(_RSA_KEY_SIZE, 'big')).decode()


def rsa_public_decrypt(encrypted_b64):
    """RSA公钥解密(PKCS1v15 Type1)，对应PHP的openssl_public_decrypt"""
    c = int.from_bytes(base64.b64decode(encrypted_b64), 'big')
    m = pow(c, _RSA_E, _RSA_N)
    padded = m.to_bytes(_RSA_KEY_SIZE, 'big')
    if padded[0] != 0 or padded[1] != 1:
        raise ValueError("无效PKCS1填充")
    idx = 2
    while idx < len(padded) and padded[idx] == 0xFF:
        idx += 1
    if idx >= len(padded) or padded[idx] != 0:
        raise ValueError("填充分隔符错误")
    return padded[idx + 1:].decode('utf-8')


def generate_guid():
    """生成设备GUID（与PHP版一致）"""
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'

    def to36(num):
        if num == 0:
            return '0'
        r = ''
        while num > 0:
            r = chars[num % 36] + r
            num //= 36
        return r

    ts = to36(round(time.time() * 1000))
    rnd = to36(random.randint(0, 2 ** 31 - 1))[:11]
    return f"{ts}_{'0' * (11 - len(rnd))}{rnd}"


# ================================================================
#  BaseSpider 兼容层
# ================================================================

try:
    from base.spider import Spider as BaseSpider
    if not hasattr(BaseSpider, 'getProxyUrl'):
        BaseSpider.getProxyUrl = lambda self: "http://127.0.0.1:9978/proxy?do=py&"
except ImportError:
    class BaseSpider:
        def getProxyUrl(self): return "http://127.0.0.1:9978/proxy?do=py&"
        def init(self, extend): pass
        def getName(self): return "CCTV"
        def getDependence(self): return []
        def isVideoFormat(self, url): return False
        def manualVideoCheck(self): return False
        def homeContent(self, f): return {}
        def homeVideoContent(self): return {}
        def categoryContent(self, *a): return {}
        def detailContent(self, d): return {}
        def searchContent(self, *a): return {}
        def searchContentPage(self, *a): return {}
        def playerContent(self, *a): return {}
        def localProxy(self, p): return []
        def destroy(self): return ""


# ================================================================
#  Spider 主类
# ================================================================

class Spider(BaseSpider):
    """央视频直播爬虫 - 纯Python版"""

    # ============ 频道配置 ============
    # UID1(uid)负责: cctv13,1,2,3,4,5,5+,7,8,9 共10个
    # UID2(uid1)负责: cctv10,11,12,14,15,16,17,4k16,4k,8k 共10个
    CHANNELS = [
        # --- UID1 组 (useruid="uid") ---
        {"tvg-id": "CCTV13", "name": "CCTV-13 新闻", "pid": "cctv13",
         "live_id": "Live1718276575708274", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV1", "name": "CCTV-1 综合", "pid": "cctv1",
         "live_id": "Live1717729995180256", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV2", "name": "CCTV-2 财经", "pid": "cctv2",
         "live_id": "Live1718261577870260", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV3", "name": "CCTV-3 综艺", "pid": "cctv3",
         "live_id": "Live1718261955077261", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV4", "name": "CCTV-4 中文国际", "pid": "cctv4",
         "live_id": "Live1718276148119264", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV5", "name": "CCTV-5 体育", "pid": "cctv5",
         "live_id": "Live1719474204987287", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV5P", "name": "CCTV-5+ 体育赛事", "pid": "cctv5p",
         "live_id": "Live1719473996025286", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV7", "name": "CCTV-7 国防军事", "pid": "cctv7",
         "live_id": "Live1718276412224269", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV8", "name": "CCTV-8 电视剧", "pid": "cctv8",
         "live_id": "Live1718276458899270", "useruid": "uid", "group": "央视"},
        {"tvg-id": "CCTV9", "name": "CCTV-9 纪录", "pid": "cctv9",
         "live_id": "Live1718276503187272", "useruid": "uid", "group": "央视"},

        # --- UID2 组 (useruid="uid1") ---
        {"tvg-id": "CCTV10", "name": "CCTV-10 科教", "pid": "cctv10",
         "live_id": "Live1718276550002273", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV11", "name": "CCTV-11 戏曲", "pid": "cctv11",
         "live_id": "Live1718276603690275", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV12", "name": "CCTV-12 社会与法", "pid": "cctv12",
         "live_id": "Live1718276623932276", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV14", "name": "CCTV-14 少儿", "pid": "cctv14",
         "live_id": "Live1718276498748271", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV15", "name": "CCTV-15 音乐", "pid": "cctv15",
         "live_id": "Live1718276319614267", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV16", "name": "CCTV-16 奥林匹克", "pid": "cctv16",
         "live_id": "Live1718276256572265", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV17", "name": "CCTV-17 农业农村", "pid": "cctv17",
         "live_id": "Live1718276138318263", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV4K16", "name": "CCTV-4K 超高清", "pid": "cctv4k16",
         "live_id": "Live1704966749996185", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV4K", "name": "CCTV-4K 测试", "pid": "cctv4k",
         "live_id": "Live1704872878572161", "useruid": "uid1", "group": "央视"},
        {"tvg-id": "CCTV8K", "name": "CCTV-8K 超高清", "pid": "cctv8k",
         "live_id": "Live1688400593818102", "useruid": "uid1", "group": "央视"},
    ]

    def __init__(self):
        super().__init__()
        self.session = None
        self.cache = OrderedDict()
        self.max_cache_size = 60
        self.uid_list = []
        self.guid_map = {}          # {uid: guid} 每个UID的设备GUID
        self.last_req_time = 0
        self.min_interval = 1.5     # API请求最小间隔(秒)
        self.req_timeout = 15
        self._req_count = 0         # 请求计数(用于定期清理缓存)
        # 缓存TTL(秒)
        self.ttl_secret = 7200      # appSecret: 2小时
        self.ttl_base = 1800        # base M3U URL: 30分钟
        self.ttl_stream = 1800      # stream URL: 30分钟
        self.ttl_m3u8 = 8           # M3U8内容: 8秒
        # 频道索引(init时构建)
        self._ch_map = {}

    def _mk_session(self):
        s = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET", "POST"])
        a = HTTPAdapter(max_retries=retry)
        s.mount("https://", a)
        s.mount("http://", a)
        return s

    def getName(self):
        return "央视频"

    def init(self, extend):
        logger.info("央视频爬虫初始化(纯Python版)")
        self.session = self._mk_session()
        self.cache.clear()
        self.guid_map.clear()
        self._req_count = 0

        # 解析ext配置
        try:
            ext = json.loads(extend) if extend else {}
        except Exception:
            ext = {}

        # 读取UID列表
        uid_cfg = ext.get('uid', [])
        if isinstance(uid_cfg, str):
            uid_cfg = [uid_cfg]
        self.uid_list = uid_cfg if uid_cfg else ["81ee2d20db46ada9"]

        # 确保至少2个UID
        if len(self.uid_list) < 2:
            logger.warning("只提供了1个UID，第二组频道将使用相同UID（可能超过10频道限制）")
            self.uid_list.append(self.uid_list[0])

        # 为每个UID生成GUID
        for uid in set(self.uid_list):
            self.guid_map[uid] = generate_guid()

        # 构建频道索引 pid -> channel_data
        self._ch_map = {ch['pid']: ch for ch in self.CHANNELS}

        logger.info(f"UID1: {self.uid_list[0]} (频道1-10)")
        logger.info(f"UID2: {self.uid_list[1]} (频道11-20)")
        logger.info(f"总频道数: {len(self.CHANNELS)}")

    # ============ 缓存管理 ============

    def _cget(self, key, ttl):
        """获取缓存，过期返回None"""
        if key in self.cache:
            e = self.cache[key]
            if time.time() - e['t'] < ttl:
                self.cache.move_to_end(key)
                return e['d']
            del self.cache[key]
        return None

    def _cset(self, key, data):
        """写入缓存，自动淘汰"""
        while len(self.cache) >= self.max_cache_size:
            self.cache.popitem(last=False)
        self.cache[key] = {'d': data, 't': time.time()}

    def _cleanup_cache(self):
        """清理过期缓存"""
        now = time.time()
        max_ttl = max(self.ttl_secret, self.ttl_base, self.ttl_stream) + 60
        expired = [k for k, v in self.cache.items() if now - v['t'] > max_ttl]
        for k in expired:
            del self.cache[k]
        if expired:
            logger.info(f"清理过期缓存: {len(expired)}条")

    # ============ 请求控制 ============

    def _throttle(self):
        """API请求间隔控制"""
        elapsed = time.time() - self.last_req_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_req_time = time.time()

    # ============ UID分配 ============

    def _uid_for(self, channel):
        """根据频道配置返回对应UID（固定分配，不轮换）"""
        if channel.get('useruid') == 'uid1':
            return self.uid_list[1] if len(self.uid_list) > 1 else self.uid_list[0]
        return self.uid_list[0]

    # ============ API调用 ============

    def _get_app_secret(self, uid):
        """获取appSecret（RSA加解密在Python中完成）"""
        ck = f"secret_{uid}"
        cached = self._cget(ck, self.ttl_secret)
        if cached:
            return cached

        try:
            guid = self.guid_map.get(uid) or generate_guid()
            encrypted_guid = rsa_public_encrypt(guid)

            self._throttle()
            resp = self.session.post(
                'https://ytpaddr.cctv.cn/gsnw/tpa/sk/obtain',
                data=json.dumps({'guid': encrypted_guid}),
                headers={
                    'Accept': 'application/json',
                    'UID': uid,
                    'Referer': 'api.cctv.cn',
                    'User-Agent': 'cctv_app_tv',
                    'Content-Type': 'application/json',
                },
                timeout=self.req_timeout,
                verify=False
            )
            resp.raise_for_status()
            result = resp.json()

            # 检查API错误
            if result.get('result') == '400':
                logger.error(f"appSecret API错误: {result.get('message', '未知')}, uid={uid}")
                return None

            enc_secret = result.get('data', {}).get('appSecret', '')
            if not enc_secret:
                logger.error(f"appSecret为空, uid={uid}")
                return None

            secret = rsa_public_decrypt(enc_secret)
            self._cset(ck, secret)
            logger.info(f"appSecret获取成功, uid={uid[:8]}...")
            return secret

        except Exception as e:
            logger.error(f"appSecret获取失败: {e}, uid={uid[:8]}...")
            return None

    def _get_base_url(self, live_id, uid):
        """获取基础M3U URL"""
        ck = f"base_{uid}_{live_id}"
        cached = self._cget(ck, self.ttl_base)
        if cached:
            return cached

        try:
            body = json.dumps({
                'rate': '', 'systemType': 'android', 'model': '',
                'id': live_id, 'userId': '', 'clientSign': 'cctvVideo',
                'deviceId': {'serial': '', 'imei': '', 'android_id': uid}
            })

            self._throttle()
            resp = self.session.post(
                'https://ytpaddr.cctv.cn/gsnw/live',
                data=body,
                headers={
                    'Accept': 'application/json', 'UID': uid,
                    'Referer': 'api.cctv.cn', 'User-Agent': 'cctv_app_tv',
                    'Content-Type': 'application/json',
                },
                timeout=self.req_timeout,
                verify=False
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get('result') == '400':
                logger.error(f"base URL API错误: {result.get('message', '')}")
                return None

            vlist = result.get('data', {}).get('videoList', [])
            url = vlist[0].get('url', '') if vlist else ''
            if url:
                self._cset(ck, url)
                logger.info(f"base URL获取成功, live_id={live_id}")
                return url

            logger.error(f"base URL为空, live_id={live_id}")
            return None

        except Exception as e:
            logger.error(f"base URL获取失败: {e}")
            return None

    def _get_stream_url(self, base_url, app_secret, uid):
        """获取流URL"""
        url_hash = hashlib.md5(base_url.encode()).hexdigest()[:12]
        ck = f"stream_{uid}_{url_hash}"
        cached = self._cget(ck, self.ttl_stream)
        if cached:
            return cached

        try:
            rnd = uuid.uuid4().hex[:13]
            sign = hashlib.md5(
                f"{_APP_ID}{app_secret}{rnd}".encode()
            ).hexdigest()

            appcommon = json.dumps({
                'adid': uid, 'av': _APP_VERSION,
                'an': '央视视频电视投屏助手', 'ap': 'cctv_app_tv'
            })

            self._throttle()
            resp = self.session.post(
                'https://ytpvdn.cctv.cn/cctvmobileinf/rest/cctv/videoliveUrl/getstream',
                data=urlencode({'appcommon': appcommon, 'url': base_url}),
                headers={
                    'User-Agent': 'cctv_app_tv', 'Referer': 'api.cctv.cn',
                    'UID': uid, 'APPID': _APP_ID,
                    'APPSIGN': sign, 'APPRANDOMSTR': rnd,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                timeout=self.req_timeout,
                verify=False
            )
            resp.raise_for_status()
            result = resp.json()

            stream_url = result.get('url', '')
            if stream_url:
                self._cset(ck, stream_url)
                logger.info("stream URL获取成功")
                return stream_url

            logger.error(f"stream URL为空, 响应: {result}")
            return None

        except Exception as e:
            logger.error(f"stream URL获取失败: {e}")
            return None

    def _fetch_m3u8(self, stream_url, uid):
        """获取M3U8内容并处理TS链接"""
        try:
            resp = self.session.get(
                stream_url,
                headers={
                    'User-Agent': 'cctv_app_tv',
                    'Referer': 'api.cctv.cn',
                    'UID': uid,
                },
                timeout=30,
                verify=False
            )
            resp.raise_for_status()
            content = resp.text

            if not content or '#EXTM3U' not in content:
                logger.error("M3U8内容无效")
                return None

            # 处理TS链接 -> 通过本地代理
            lines = content.split('\n')
            processed = []
            for line in lines:
                s = line.strip()
                if s and not s.startswith('#') and '.ts' in s:
                    # 构建完整TS URL
                    if s.startswith('http'):
                        ts_url = s
                    else:
                        # 相对路径，拼接CDN域名
                        if '?' in s:
                            fname, params = s.split('?', 1)
                            ts_url = f"http://liveali-tpgq.cctv.cn/live/{fname}?{params}"
                        else:
                            ts_url = f"http://liveali-tpgq.cctv.cn/live/{s}"

                    enc = self._b64e(ts_url)
                    processed.append(
                        f"http://127.0.0.1:9978/proxy?do=py&type=ts&url={enc}&uid={uid}"
                    )
                else:
                    processed.append(line)

            return '\n'.join(processed)

        except Exception as e:
            logger.error(f"M3U8获取失败: {e}")
            return None

    # ============ tvbox接口 ============

    def liveContent(self, url):
        """生成频道列表"""
        try:
            lines = ['#EXTM3U']
            for ch in self.CHANNELS:
                proxy = f"http://127.0.0.1:9978/proxy?do=py&fun=cctv&pid={ch['pid']}"
                lines.append(
                    f'#EXTINF:-1 tvg-id="{ch["tvg-id"]}" tvg-name="{ch["tvg-id"]}" '
                    f'tvg-logo="" group-title="{ch["group"]}",{ch["name"]}'
                )
                lines.append(proxy)
            logger.info(f"频道列表生成: {len(self.CHANNELS)}个频道")
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"频道列表生成失败: {e}")
            return '#EXTM3U\n#EXTINF:-1,错误\nhttp://127.0.0.1'

    def localProxy(self, params):
        """代理入口"""
        fun = params.get('fun')
        typ = params.get('type')
        try:
            if fun == 'cctv':
                return self._handle_channel(params)
            elif typ == 'ts':
                return self._handle_ts(params)
        except Exception as e:
            logger.error(f"代理异常: {e}")
        return self._err("处理失败")

    def _handle_channel(self, params):
        """处理频道请求（核心逻辑，无UID轮换）"""
        pid = params.get('pid')
        if not pid:
            return self._err("缺少频道ID")

        # 每50次请求清理一次过期缓存
        self._req_count += 1
        if self._req_count % 50 == 0:
            self._cleanup_cache()

        # M3U8短期缓存
        m3u8_ck = f"m3u8_{pid}"
        cached = self._cget(m3u8_ck, self.ttl_m3u8)
        if cached:
            return [200, "application/vnd.apple.mpegurl", cached]

        # 查找频道
        channel = self._ch_map.get(pid)
        if not channel:
            return self._err(f"频道不存在: {pid}")

        # 获取该频道固定分配的UID（不轮换）
        uid = self._uid_for(channel)
        live_id = channel['live_id']
        logger.info(f"请求频道: {pid}, uid={uid[:8]}...")

        # 1. 获取appSecret
        secret = self._get_app_secret(uid)
        if not secret:
            return self._err(f"密钥获取失败: {pid}")

        # 2. 获取base URL
        base_url = self._get_base_url(live_id, uid)
        if not base_url:
            return self._err(f"地址获取失败: {pid}")

        # 3. 获取stream URL
        stream_url = self._get_stream_url(base_url, secret, uid)
        if not stream_url:
            return self._err(f"流获取失败: {pid}")

        # 4. 获取并处理M3U8
        m3u8 = self._fetch_m3u8(stream_url, uid)
        if not m3u8:
            return self._err(f"内容获取失败: {pid}")

        self._cset(m3u8_ck, m3u8)
        logger.info(f"频道成功: {pid}")
        return [200, "application/vnd.apple.mpegurl", m3u8]

    def _handle_ts(self, params):
        """代理获取TS片段"""
        try:
            url = self._b64d(params.get('url', ''))
            uid = params.get('uid', '')
            if not url:
                return self._err("TS URL为空")

            host = urlparse(url).hostname or 'liveali-tpgq.cctv.cn'
            resp = self.session.get(
                url,
                headers={
                    'User-Agent': 'cctv_app_tv',
                    'Referer': 'api.cctv.cn',
                    'UID': uid,
                    'Host': host,
                    'Accept': '*/*',
                    'Connection': 'keep-alive'
                },
                timeout=15,
                verify=False
            )
            resp.raise_for_status()
            data = resp.content

            return [200, "video/MP2T", data, {
                'Content-Type': 'video/MP2T',
                'Content-Length': str(len(data)),
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            }]

        except Exception as e:
            logger.error(f"TS获取失败: {e}")
            return self._err(f"TS失败")

    # ============ 工具方法 ============

    def _b64e(self, data):
        try:
            return base64.urlsafe_b64encode(data.encode()).decode().rstrip('=')
        except Exception:
            return ""

    def _b64d(self, data):
        try:
            pad = 4 - (len(data) % 4)
            if pad != 4:
                data += '=' * pad
            return base64.urlsafe_b64decode(data.encode()).decode()
        except Exception:
            return ""

    def _err(self, msg):
        return [500, "application/vnd.apple.mpegurl",
                f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:0\n"
                f"#EXT-X-TARGETDURATION:10\n#EXTINF:10.0,\nerror.ts\n"
                f"#EXT-X-ENDLIST\n# {msg}"]

    def destroy(self):
        try:
            if self.session:
                self.session.close()
                self.session = None
            self.cache.clear()
            self.guid_map.clear()
            self._ch_map.clear()
            logger.info("资源已释放，缓存已清理")
        except Exception:
            pass
        return ""


# ================================================================
#  测试代码
# ================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("央视频爬虫测试（纯Python版，无PHP依赖）")
    print("=" * 60)

    spider = Spider()
    spider.init(json.dumps({
        "uid": ["81ee2d20db46ada9", "81ee2d20db46ada9"]
    }))

    # 测试RSA
    print("\n[1] RSA加解密测试:")
    try:
        test_data = "test_guid_12345"
        encrypted = rsa_public_encrypt(test_data)
        print(f"  加密成功: {encrypted[:40]}...")
        print("  ✓ RSA公钥加密正常")
    except Exception as e:
        print(f"  ✗ RSA加密失败: {e}")

    # 测试GUID生成
    print("\n[2] GUID生成测试:")
    guid = generate_guid()
    print(f"  GUID: {guid}")
    print("  ✓ GUID生成正常")

    # 测试频道列表
    print("\n[3] 频道列表测试:")
    content = spider.liveContent("")
    ch_count = content.count('#EXTINF')
    print(f"  频道数: {ch_count}")
    print(f"  预览:\n{content[:300]}...")

    # 测试频道获取
    print("\n[4] CCTV1频道测试:")
    result = spider._handle_channel({'pid': 'cctv1'})
    if result[0] == 200:
        print("  ✓ CCTV1获取成功")
        ts_count = result[2].count('proxy?do=py&type=ts')
        print(f"  TS代理链接数: {ts_count}")
        print(f"  M3U8预览:\n{result[2][:400]}...")
    else:
        print(f"  ✗ CCTV1获取失败: {result[2][-100:]}")

    # 测试UID2组频道
    print("\n[5] CCTV10频道测试(UID2):")
    result2 = spider._handle_channel({'pid': 'cctv10'})
    if result2[0] == 200:
        print("  ✓ CCTV10获取成功")
    else:
        print(f"  ✗ CCTV10获取失败")

    spider.destroy()
    print("\n测试完成")
