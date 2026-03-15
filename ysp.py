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
#  RSA 工具
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
    pos = [0]
    def rb():
        b = der_bytes[pos[0]]; pos[0] += 1; return b
    def read_len():
        b = rb()
        if b & 0x80 == 0: return b
        cnt = b & 0x7f; length = 0
        for _ in range(cnt): length = (length << 8) | rb()
        return length
    def read_int():
        if rb() != 0x02: raise ValueError("非INTEGER")
        ln = read_len()
        val = int.from_bytes(der_bytes[pos[0]:pos[0]+ln], 'big')
        pos[0] += ln; return val
    rb(); read_len()
    rb(); algo_len = read_len(); pos[0] += algo_len
    rb(); read_len(); rb()
    rb(); read_len()
    return read_int(), read_int()


try:
    _RSA_N, _RSA_E = _parse_der_public_key(base64.b64decode(_PUB_KEY_B64))
    _RSA_KEY_SIZE = (_RSA_N.bit_length() + 7) // 8
except Exception as _e:
    logger.error(f"RSA公钥加载失败: {_e}")
    _RSA_N = _RSA_E = _RSA_KEY_SIZE = None


def rsa_public_encrypt(data):
    if isinstance(data, str): data = data.encode('utf-8')
    pad_len = _RSA_KEY_SIZE - len(data) - 3
    if pad_len < 8: raise ValueError("数据过长")
    pad = bytearray()
    while len(pad) < pad_len:
        b = os.urandom(1)[0]
        if b != 0: pad.append(b)
    m = int.from_bytes(b'\x00\x02' + bytes(pad) + b'\x00' + data, 'big')
    c = pow(m, _RSA_E, _RSA_N)
    return base64.b64encode(c.to_bytes(_RSA_KEY_SIZE, 'big')).decode()


def rsa_public_decrypt(encrypted_b64):
    c = int.from_bytes(base64.b64decode(encrypted_b64), 'big')
    m = pow(c, _RSA_E, _RSA_N)
    padded = m.to_bytes(_RSA_KEY_SIZE, 'big')
    if padded[0] != 0 or padded[1] != 1: raise ValueError("无效PKCS1")
    idx = 2
    while idx < len(padded) and padded[idx] == 0xFF: idx += 1
    if idx >= len(padded) or padded[idx] != 0: raise ValueError("填充错误")
    return padded[idx+1:].decode('utf-8')


def generate_guid():
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    def to36(num):
        if num == 0: return '0'
        r = ''
        while num > 0: r = chars[num % 36] + r; num //= 36
        return r
    ts = to36(round(time.time() * 1000))
    rnd = to36(random.randint(0, 2**31-1))[:11]
    return f"{ts}_{'0'*(11-len(rnd))}{rnd}"


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
        def init(self, e): pass
        def getName(self): return "CCTV"
        def getDependence(self): return []
        def isVideoFormat(self, u): return False
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
#  网络UID管理器
# ================================================================

class RemoteUidManager:
    """通过远程PHP管理UID的分配、心跳、释放、失效上报"""

    def __init__(self, server_url, device_id, session):
        self.server = server_url.rstrip('/')
        self.device_id = device_id
        self.session = session
        self.allocated_uids = {}  # {slot: uid}  slot='uid' or 'uid1'
        self.last_heartbeat = 0
        self.heartbeat_interval = 300  # 5分钟心跳

    def _call(self, action, extra=None):
        """调用远程PHP API"""
        data = {
            'action': action,
            'device_id': self.device_id,
            'secret': 'ysp_uid_2024'  # 简单鉴权密钥
        }
        if extra:
            data.update(extra)
        try:
            resp = self.session.post(
                self.server,
                data=data,
                headers={'User-Agent': 'ysp_py_client/1.0'},
                timeout=10,
                verify=False
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get('code') == 0:
                return result.get('data')
            else:
                logger.warning(f"UID服务器返回错误: {result.get('msg', '未知')}")
                return None
        except Exception as e:
            logger.error(f"UID服务器通信失败: {e}")
            return None

    def allocate(self, count=2):
        """申请分配UID（请求count个）"""
        result = self._call('allocate', {'count': str(count)})
        if result and isinstance(result, dict):
            uids = result.get('uids', [])
            if len(uids) >= 1:
                self.allocated_uids['uid'] = uids[0]
            if len(uids) >= 2:
                self.allocated_uids['uid1'] = uids[1]
            elif len(uids) == 1:
                # 只分到1个UID，两组频道共用
                self.allocated_uids['uid1'] = uids[0]
            logger.info(f"远程分配UID: {self.allocated_uids}")
            self.last_heartbeat = time.time()
            return True
        logger.error("远程UID分配失败")
        return False

    def heartbeat(self):
        """发送心跳（维持占用状态）"""
        now = time.time()
        if now - self.last_heartbeat < self.heartbeat_interval:
            return True
        uids = list(set(self.allocated_uids.values()))
        if not uids:
            return False
        result = self._call('heartbeat', {'uids': json.dumps(uids)})
        if result is not None:
            self.last_heartbeat = now
            logger.debug("心跳成功")
            return True
        logger.warning("心跳失败")
        return False

    def release(self):
        """释放所有分配的UID"""
        uids = list(set(self.allocated_uids.values()))
        if uids:
            self._call('release', {'uids': json.dumps(uids)})
            logger.info(f"已释放UID: {uids}")
        self.allocated_uids.clear()

    def report_failed(self, uid):
        """上报UID失效"""
        self._call('report_failed', {'failed_uid': uid})
        logger.info(f"已上报UID失效: {uid}")

    def get_uid(self, slot):
        """获取指定slot的UID"""
        return self.allocated_uids.get(slot)

    def has_uids(self):
        return bool(self.allocated_uids)


# ================================================================
#  Spider 主类
# ================================================================

class Spider(BaseSpider):
    """央视频直播爬虫 - 本地+网络UID模式"""

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
        self.guid_map = {}
        self.last_req_time = 0
        self.min_interval = 1.5
        self.req_timeout = 15
        self._req_count = 0
        self._ch_map = {}
        # 模式
        self.mode = 'local'  # 'local' 或 'remote'
        self.uid_manager = None
        # 失效UID记录(本地模式)
        self.failed_uids = {}  # {uid: fail_timestamp}
        self.fail_cooldown = 600  # 本地模式失效冷却10分钟
        # 缓存TTL
        self.ttl_secret = 7200
        self.ttl_base = 1800
        self.ttl_stream = 1800
        self.ttl_m3u8 = 8

    def _mk_session(self):
        s = requests.Session()
        retry = Retry(total=2, backoff_factor=0.5,
                      status_forcelist=[429, 500, 502, 503, 504],
                      allowed_methods=["GET", "POST"])
        a = HTTPAdapter(max_retries=retry)
        s.mount("https://", a)
        s.mount("http://", a)
        return s

    def getName(self): return "央视频"

    def init(self, extend):
        logger.info("央视频爬虫初始化")
        self.session = self._mk_session()
        self.cache.clear()
        self.guid_map.clear()
        self.failed_uids.clear()
        self._req_count = 0

        try:
            ext = json.loads(extend) if extend else {}
        except Exception:
            ext = {}

        # 构建频道索引
        self._ch_map = {ch['pid']: ch for ch in self.CHANNELS}

        # 判断模式
        uid_cfg = ext.get('uid', [])
        if isinstance(uid_cfg, str):
            uid_cfg = [uid_cfg]
        uid_server = ext.get('uid_server', '')

        if uid_cfg and uid_cfg[0]:
            # ===== 本地模式 =====
            self.mode = 'local'
            self.uid_list = uid_cfg
            if len(self.uid_list) < 2:
                self.uid_list.append(self.uid_list[0])
            for uid in set(self.uid_list):
                self.guid_map[uid] = generate_guid()
            logger.info(f"[本地模式] UID1={self.uid_list[0][:8]}..., UID2={self.uid_list[1][:8]}...")

        elif uid_server:
            # ===== 网络模式 =====
            self.mode = 'remote'
            device_id = ext.get('device_id', uuid.uuid4().hex[:16])
            self.uid_manager = RemoteUidManager(uid_server, device_id, self.session)
            # 分配UID
            if self.uid_manager.allocate(2):
                uid1 = self.uid_manager.get_uid('uid') or ''
                uid2 = self.uid_manager.get_uid('uid1') or uid1
                self.uid_list = [uid1, uid2]
                for uid in set(self.uid_list):
                    if uid:
                        self.guid_map[uid] = generate_guid()
                logger.info(f"[网络模式] 分配UID1={uid1[:8]}..., UID2={uid2[:8]}...")
            else:
                logger.error("[网络模式] UID分配失败，降级为空UID")
                self.uid_list = []
        else:
            # 无配置
            logger.warning("未配置uid或uid_server，频道将不可用")
            self.mode = 'local'
            self.uid_list = []

        logger.info(f"模式={self.mode}, 频道数={len(self.CHANNELS)}")

    # ============ 缓存 ============

    def _cget(self, key, ttl):
        if key in self.cache:
            e = self.cache[key]
            if time.time() - e['t'] < ttl:
                self.cache.move_to_end(key)
                return e['d']
            del self.cache[key]
        return None

    def _cset(self, key, data):
        while len(self.cache) >= self.max_cache_size:
            self.cache.popitem(last=False)
        self.cache[key] = {'d': data, 't': time.time()}

    def _cleanup(self):
        now = time.time()
        max_ttl = max(self.ttl_secret, self.ttl_base, self.ttl_stream) + 60
        expired = [k for k, v in self.cache.items() if now - v['t'] > max_ttl]
        for k in expired:
            del self.cache[k]

    # ============ 请求控制 ============

    def _throttle(self):
        elapsed = time.time() - self.last_req_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_req_time = time.time()

    # ============ UID分配 ============

    def _uid_for(self, channel):
        """获取频道对应的UID"""
        if not self.uid_list:
            return None
        if channel.get('useruid') == 'uid1':
            return self.uid_list[1] if len(self.uid_list) > 1 else self.uid_list[0]
        return self.uid_list[0]

    def _is_uid_failed(self, uid):
        """检查UID是否在失效冷却期"""
        if uid in self.failed_uids:
            if time.time() - self.failed_uids[uid] < self.fail_cooldown:
                return True
            del self.failed_uids[uid]
        return False

    def _mark_uid_failed(self, uid):
        """标记UID失效"""
        self.failed_uids[uid] = time.time()
        logger.warning(f"标记UID失效: {uid[:8]}...")
        # 网络模式下上报失效
        if self.mode == 'remote' and self.uid_manager:
            self.uid_manager.report_failed(uid)

    # ============ API调用 ============

    def _get_app_secret(self, uid):
        ck = f"secret_{uid}"
        cached = self._cget(ck, self.ttl_secret)
        if cached: return cached

        try:
            guid = self.guid_map.get(uid)
            if not guid:
                guid = generate_guid()
                self.guid_map[uid] = guid
            encrypted_guid = rsa_public_encrypt(guid)

            self._throttle()
            resp = self.session.post(
                'https://ytpaddr.cctv.cn/gsnw/tpa/sk/obtain',
                data=json.dumps({'guid': encrypted_guid}),
                headers={
                    'Accept': 'application/json', 'UID': uid,
                    'Referer': 'api.cctv.cn', 'User-Agent': 'cctv_app_tv',
                    'Content-Type': 'application/json',
                },
                timeout=self.req_timeout, verify=False
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get('result') == '400':
                logger.error(f"appSecret错误: {result.get('message', '')}")
                self._mark_uid_failed(uid)
                return None

            enc = result.get('data', {}).get('appSecret', '')
            if not enc:
                logger.error("appSecret为空")
                return None

            secret = rsa_public_decrypt(enc)
            self._cset(ck, secret)
            return secret
        except Exception as e:
            logger.error(f"appSecret失败: {e}")
            return None

    def _get_base_url(self, live_id, uid):
        ck = f"base_{uid}_{live_id}"
        cached = self._cget(ck, self.ttl_base)
        if cached: return cached

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
                timeout=self.req_timeout, verify=False
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get('result') == '400':
                self._mark_uid_failed(uid)
                return None
            vlist = result.get('data', {}).get('videoList', [])
            url = vlist[0].get('url', '') if vlist else ''
            if url:
                self._cset(ck, url)
                return url
            return None
        except Exception as e:
            logger.error(f"base URL失败: {e}")
            return None

    def _get_stream_url(self, base_url, app_secret, uid):
        url_hash = hashlib.md5(base_url.encode()).hexdigest()[:12]
        ck = f"stream_{uid}_{url_hash}"
        cached = self._cget(ck, self.ttl_stream)
        if cached: return cached

        try:
            rnd = uuid.uuid4().hex[:13]
            sign = hashlib.md5(f"{_APP_ID}{app_secret}{rnd}".encode()).hexdigest()
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
                timeout=self.req_timeout, verify=False
            )
            resp.raise_for_status()
            result = resp.json()
            surl = result.get('url', '')
            if surl:
                self._cset(ck, surl)
                return surl
            return None
        except Exception as e:
            logger.error(f"stream URL失败: {e}")
            return None

    def _fetch_m3u8(self, stream_url, uid):
        try:
            resp = self.session.get(
                stream_url,
                headers={
                    'User-Agent': 'cctv_app_tv',
                    'Referer': 'api.cctv.cn', 'UID': uid,
                },
                timeout=30, verify=False
            )
            resp.raise_for_status()
            content = resp.text
            if not content or '#EXTM3U' not in content:
                return None

            lines = content.split('\n')
            processed = []
            for line in lines:
                s = line.strip()
                if s and not s.startswith('#') and '.ts' in s:
                    if s.startswith('http'):
                        ts_url = s
                    else:
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
        try:
            lines = ['#EXTM3U']
            for ch in self.CHANNELS:
                proxy = f"http://127.0.0.1:9978/proxy?do=py&fun=cctv&pid={ch['pid']}"
                lines.append(
                    f'#EXTINF:-1 tvg-id="{ch["tvg-id"]}" tvg-name="{ch["tvg-id"]}" '
                    f'tvg-logo="" group-title="{ch["group"]}",{ch["name"]}'
                )
                lines.append(proxy)
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"频道列表失败: {e}")
            return '#EXTM3U\n#EXTINF:-1,错误\nhttp://127.0.0.1'

    def localProxy(self, params):
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
        """处理频道请求"""
        pid = params.get('pid')
        if not pid:
            return self._err("缺少频道ID")

        # 定期清理缓存 + 网络模式心跳
        self._req_count += 1
        if self._req_count % 50 == 0:
            self._cleanup()
        if self._req_count % 30 == 0 and self.mode == 'remote' and self.uid_manager:
            self.uid_manager.heartbeat()

        # M3U8短期缓存
        m3u8_ck = f"m3u8_{pid}"
        cached = self._cget(m3u8_ck, self.ttl_m3u8)
        if cached:
            return [200, "application/vnd.apple.mpegurl", cached]

        channel = self._ch_map.get(pid)
        if not channel:
            return self._err(f"频道不存在: {pid}")

        uid = self._uid_for(channel)
        if not uid:
            return self._err("无可用UID")

        # 检查UID是否在失效冷却期
        if self._is_uid_failed(uid):
            logger.warning(f"UID在冷却期，跳过: {pid}, uid={uid[:8]}...")
            return self._err(f"UID暂时不可用: {pid}")

        live_id = channel['live_id']
        logger.info(f"频道请求: {pid}, uid={uid[:8]}...")

        # 1. appSecret
        secret = self._get_app_secret(uid)
        if not secret:
            return self._err(f"密钥获取失败: {pid}")

        # 2. base URL
        base_url = self._get_base_url(live_id, uid)
        if not base_url:
            return self._err(f"地址获取失败: {pid}")

        # 3. stream URL
        stream_url = self._get_stream_url(base_url, secret, uid)
        if not stream_url:
            return self._err(f"流获取失败: {pid}")

        # 4. M3U8
        m3u8 = self._fetch_m3u8(stream_url, uid)
        if not m3u8:
            return self._err(f"内容获取失败: {pid}")

        self._cset(m3u8_ck, m3u8)
        return [200, "application/vnd.apple.mpegurl", m3u8]

    def _handle_ts(self, params):
        try:
            url = self._b64d(params.get('url', ''))
            uid = params.get('uid', '')
            if not url:
                return self._err("TS URL为空")
            host = urlparse(url).hostname or 'liveali-tpgq.cctv.cn'
            resp = self.session.get(
                url,
                headers={
                    'User-Agent': 'cctv_app_tv', 'Referer': 'api.cctv.cn',
                    'UID': uid, 'Host': host,
                    'Accept': '*/*', 'Connection': 'keep-alive'
                },
                timeout=15, verify=False
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
            logger.error(f"TS失败: {e}")
            return self._err("TS获取失败")

    # ============ 工具 ============

    def _b64e(self, data):
        try:
            return base64.urlsafe_b64encode(data.encode()).decode().rstrip('=')
        except Exception: return ""

    def _b64d(self, data):
        try:
            pad = 4 - (len(data) % 4)
            if pad != 4: data += '=' * pad
            return base64.urlsafe_b64decode(data.encode()).decode()
        except Exception: return ""

    def _err(self, msg):
        return [500, "application/vnd.apple.mpegurl",
                f"#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-MEDIA-SEQUENCE:0\n"
                f"#EXT-X-TARGETDURATION:10\n#EXTINF:10.0,\nerror.ts\n"
                f"#EXT-X-ENDLIST\n# {msg}"]

    def destroy(self):
        try:
            # 网络模式释放UID
            if self.mode == 'remote' and self.uid_manager:
                self.uid_manager.release()
            if self.session:
                self.session.close()
                self.session = None
            self.cache.clear()
            self.guid_map.clear()
            self._ch_map.clear()
            self.failed_uids.clear()
            logger.info("资源释放完成")
        except Exception:
            pass
        return ""


# ================================================================
#  测试
# ================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("央视频爬虫测试")
    print("=" * 60)

    # 本地模式测试
    print("\n[本地模式测试]")
    spider = Spider()
    spider.init(json.dumps({
        "uid": ["81ee2d20db46ada9", "81ee2d20db46ada9"]
    }))
    print(f"模式: {spider.mode}")
    result = spider._handle_channel({'pid': 'cctv1'})
    print(f"CCTV1: {'成功' if result[0]==200 else '失败'}")
    if result[0] == 200:
        ts_count = result[2].count('type=ts')
        print(f"TS片段数: {ts_count}")
    spider.destroy()

    # 网络模式测试(需要PHP服务器)
    # print("\n[网络模式测试]")
    # spider2 = Spider()
    # spider2.init(json.dumps({
    #     "uid_server": "https://你的域名/uid_manager.php",
    #     "device_id": "test_device_001"
    # }))
    # result2 = spider2._handle_channel({'pid': 'cctv1'})
    # print(f"CCTV1: {'成功' if result2[0]==200 else '失败'}")
    # spider2.destroy()

    print("\n测试完成")
