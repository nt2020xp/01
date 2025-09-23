from typing import Optional, AsyncIterator

import time
import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse, StreamingResponse

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class Spider:
    def __init__(self) -> None:
        self._load_channels()
        self.key = "QnBECDd6L9C65VYw"
        self.iv = "IwM2QIh7HKUTETbI"

    def channel_master_playlist(self, request: Request) -> str:
        base = self._proxy_base(request)
        lines = ["#EXTM3U"]
        for ch in self.channels:
            lines.append(
                (
                    f'#EXTINF:-1 tvg-id="{ch["tvg-id"]}" '
                    f'tvg-name="{ch["tvg-name"]}" '
                    f'tvg-logo="{ch["tvg-logo"]}" '
                    f'group-title="{ch["group-title"]}",{ch["name"]}'
                )
            )
            lines.append(f"{base}?type=m3u8&pid={ch['pid']}")
        return "\n".join(lines)

    def build_segment_playlist(self, pid: str) -> str:
        a, b, c = pid.split(",")
        ts_now = int(time.time() / 4 - 355_017_625)
        t = ts_now * 4

        head = (
            "#EXTM3U\n#EXT-X-VERSION:3\n"
            "#EXT-X-TARGETDURATION:4\n"
            f"#EXT-X-MEDIA-SEQUENCE:{ts_now}\n"
        )
        body = []
        for seq in range(10):
            url = (
                "https://ntd-tgc.cdn.hinet.net/live/pool/"
                f"{a}/litv-pc/{a}-avc1_6000000={b}-mp4a_134000_zho={c}-"
                f"begin={t}0000000-dur=40000000-seq={ts_now}.ts"
            )
            body.append("#EXTINF:4,")
            body.append(url)
            t += 4
            ts_now += 1
        return head + "\n".join(body) + "\n"

    async def fetch_ts_stream(self, enc: str) -> AsyncIterator[bytes]:
        url = self.decrypt(enc)
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=10) as client:
            async with client.stream("GET", url, headers=headers) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    yield chunk

    def encrypt(self, raw: str) -> str:
        cipher = AES.new(self.key.encode(), AES.MODE_CBC, self.iv.encode())
        return cipher.encrypt(pad(raw.encode(), AES.block_size)).hex()

    def decrypt(self, enc: str) -> str:
        cipher = AES.new(self.key.encode(), AES.MODE_CBC, self.iv.encode())
        return unpad(cipher.decrypt(bytes.fromhex(enc)), AES.block_size).decode()

    @staticmethod
    def _proxy_base(request: Request) -> str:
        return str(request.base_url) + "proxy"

    def _load_channels(self) -> None:
        self.channels = [{"tvg-id": "4gtv-4gtv002", "tvg-name": "民视", "tvg-logo": "https://logo.doube.eu.org/民视.png", "group-title": "", "name": "民视", "pid": "4gtv-4gtv002,1,10"}, {"tvg-id": "4gtv-4gtv001", "tvg-name": "民视台湾台", "tvg-logo": "https://logo.doube.eu.org/民视台湾台.png", "group-title": "", "name": "民视台湾台", "pid": "4gtv-4gtv001,1,6"}, {"tvg-id": "4gtv-4gtv156", "tvg-name": "民视台湾台", "tvg-logo": "https://logo.doube.eu.org/民视台湾台.png", "group-title": "", "name": "民视台湾台", "pid": "4gtv-4gtv156,1,6"}, {"tvg-id": "4gtv-4gtv003", "tvg-name": "民视第一台", "tvg-logo": "https://logo.doube.eu.org/民视第一台.png", "group-title": "", "name": "民视第一台", "pid": "4gtv-4gtv003,1,6"}, {"tvg-id": "litv-ftv13", "tvg-name": "民视新闻台", "tvg-logo": "https://logo.doube.eu.org/民视新闻台.png", "group-title": "", "name": "民视新闻台", "pid": "litv-ftv13,1,7"}, {"tvg-id": "litv-ftv07", "tvg-name": "民视旅游台", "tvg-logo": "https://logo.doube.eu.org/民视旅游台.png", "group-title": "", "name": "民视旅游", "pid": "litv-ftv07,1,7"}, {"tvg-id": "litv-ftv09", "tvg-name": "民视影剧台", "tvg-logo": "https://logo.doube.eu.org/民视影剧台.png", "group-title": "", "name": "民视影剧", "pid": "litv-ftv09,1,2"}, {"tvg-id": "litv-ftv09", "tvg-name": "民视影剧台", "tvg-logo": "https://logo.doube.eu.org/民视影剧台.png", "group-title": "", "name": "民视影剧", "pid": "litv-ftv09,1,7"}, {"tvg-id": "4gtv-4gtv004", "tvg-name": "民视综艺台", "tvg-logo": "https://logo.doube.eu.org/民视综艺台.png", "group-title": "", "name": "民视综艺", "pid": "4gtv-4gtv004,1,8"}, {"tvg-id": "litv-longturn22", "tvg-name": "台湾戏剧台", "tvg-logo": "https://logo.doube.eu.org/台湾戏剧台.png", "group-title": "", "name": "台湾戏剧台", "pid": "litv-longturn22,5,2"}, {"tvg-id": "litv-longturn21", "tvg-name": "龙华经典台", "tvg-logo": "https://logo.doube.eu.org/龙华经典台.png", "group-title": "", "name": "龙华经典", "pid": "litv-longturn21,5,2"}, {"tvg-id": "litv-longturn18", "tvg-name": "龙华戏剧台", "tvg-logo": "https://logo.doube.eu.org/龙华戏剧台.png", "group-title": "", "name": "龙华戏剧", "pid": "litv-longturn18,5,6"}, {"tvg-id": "litv-longturn03", "tvg-name": "龙华电影台", "tvg-logo": "https://logo.doube.eu.org/龙华电影台.png", "group-title": "", "name": "龙华电影", "pid": "litv-longturn03,5,6"}, {"tvg-id": "litv-longturn11", "tvg-name": "龙华日韩台", "tvg-logo": "https://logo.doube.eu.org/龙华日韩台.png", "group-title": "", "name": "龙华日韩", "pid": "litv-longturn11,5,2"}, {"tvg-id": "litv-longturn12", "tvg-name": "龙华偶像台", "tvg-logo": "https://logo.doube.eu.org/龙华偶像台.png", "group-title": "", "name": "龙华偶像", "pid": "litv-longturn12,5,2"}, {"tvg-id": "litv-longturn01", "tvg-name": "龙华卡通台", "tvg-logo": "https://logo.doube.eu.org/龙华卡通台.png", "group-title": "", "name": "龙华卡通", "pid": "litv-longturn01,4,2"}, {"tvg-id": "litv-longturn01", "tvg-name": "龙华卡通台", "tvg-logo": "https://logo.doube.eu.org/龙华卡通台.png", "group-title": "", "name": "龙华卡通", "pid": "litv-longturn01,4,5"}, {"tvg-id": "4gtv-4gtv046", "tvg-name": "靖天综合台", "tvg-logo": "https://logo.doube.eu.org/靖天综合台.png", "group-title": "", "name": "靖天综合台", "pid": "4gtv-4gtv046,1,8"}, {"tvg-id": "4gtv-4gtv047", "tvg-name": "靖天日本台", "tvg-logo": "https://logo.doube.eu.org/靖天日本台.png", "group-title": "", "name": "靖天日本台", "pid": "4gtv-4gtv047,1,8"}, {"tvg-id": "4gtv-4gtv054", "tvg-name": "靖天欢乐台", "tvg-logo": "https://logo.doube.eu.org/靖天欢乐台.png", "group-title": "", "name": "靖天欢乐台", "pid": "4gtv-4gtv054,1,8"}, {"tvg-id": "4gtv-4gtv055", "tvg-name": "靖天映画", "tvg-logo": "https://logo.doube.eu.org/靖天映画.png", "group-title": "", "name": "靖天映画", "pid": "4gtv-4gtv055,1,8"}, {"tvg-id": "4gtv-4gtv061", "tvg-name": "靖天电影台", "tvg-logo": "https://logo.doube.eu.org/靖天电影台.png", "group-title": "", "name": "靖天电影台", "pid": "4gtv-4gtv061,1,7"}, {"tvg-id": "4gtv-4gtv062", "tvg-name": "靖天育乐台", "tvg-logo": "https://logo.doube.eu.org/靖天育乐台.png", "group-title": "", "name": "靖天育乐台", "pid": "4gtv-4gtv062,1,8"}, {"tvg-id": "4gtv-4gtv063", "tvg-name": "靖天国际台", "tvg-logo": "https://logo.doube.eu.org/靖天国际台.png", "group-title": "", "name": "靖天国际台", "pid": "4gtv-4gtv063,1,6"}, {"tvg-id": "4gtv-4gtv058", "tvg-name": "靖天戏剧台", "tvg-logo": "https://logo.doube.eu.org/靖天戏剧台.png", "group-title": "", "name": "靖天戏剧台", "pid": "4gtv-4gtv058,1,8"}, {"tvg-id": "4gtv-4gtv065", "tvg-name": "靖天资讯台", "tvg-logo": "https://logo.doube.eu.org/靖天资讯台.png", "group-title": "", "name": "靖天资讯台", "pid": "4gtv-4gtv065,1,8"}, {"tvg-id": "4gtv-4gtv044", "tvg-name": "靖天卡通台", "tvg-logo": "https://logo.doube.eu.org/靖天卡通台.png", "group-title": "", "name": "靖天卡通台", "pid": "4gtv-4gtv044,1,8"}, {"tvg-id": "4gtv-4gtv073", "tvg-name": "TVBS", "tvg-logo": "https://logo.doube.eu.org/TVBS.png", "group-title": "", "name": "Tvbs", "pid": "4gtv-4gtv073,1,2"}, {"tvg-id": "4gtv-4gtv072", "tvg-name": "TVBS新闻", "tvg-logo": "https://logo.doube.eu.org/TVBS新闻.png", "group-title": "", "name": "Tvbs新闻台", "pid": "4gtv-4gtv072,1,2"}, {"tvg-id": "4gtv-4gtv067", "tvg-name": "TVBS精采台", "tvg-logo": "https://logo.doube.eu.org/TVBS精采台.png", "group-title": "", "name": "Tvbs精采台", "pid": "4gtv-4gtv067,1,8"}, {"tvg-id": "4gtv-4gtv068", "tvg-name": "TVBS欢乐台", "tvg-logo": "https://logo.doube.eu.org/TVBS欢乐台.png", "group-title": "", "name": "Tvbs欢乐台", "pid": "4gtv-4gtv068,1,7"}, {"tvg-id": "4gtv-4gtv066", "tvg-name": "台视", "tvg-logo": "https://logo.doube.eu.org/台视.png", "group-title": "", "name": "台视", "pid": "4gtv-4gtv066,1,2"}, {"tvg-id": "4gtv-4gtv066", "tvg-name": "台视", "tvg-logo": "https://logo.doube.eu.org/台视.png", "group-title": "", "name": "台视", "pid": "4gtv-4gtv066,1,6"}, {"tvg-id": "4gtv-4gtv056", "tvg-name": "台视财经台", "tvg-logo": "https://logo.doube.eu.org/台视财经台.png", "group-title": "", "name": "台视财经", "pid": "4gtv-4gtv056,1,2"}, {"tvg-id": "4gtv-4gtv051", "tvg-name": "台视新闻台", "tvg-logo": "https://logo.doube.eu.org/台视新闻台.png", "group-title": "", "name": "台视新闻", "pid": "4gtv-4gtv051,1,2"}, {"tvg-id": "4gtv-4gtv051", "tvg-name": "台视新闻台", "tvg-logo": "https://logo.doube.eu.org/台视新闻台.png", "group-title": "", "name": "台视新闻", "pid": "4gtv-4gtv051,1,6"}, {"tvg-id": "litv-longturn04", "tvg-name": "博斯魅力", "tvg-logo": "https://logo.doube.eu.org/博斯魅力.png", "group-title": "", "name": "博斯魅力", "pid": "litv-longturn04,5,2"}, {"tvg-id": "litv-longturn05", "tvg-name": "博斯高球1", "tvg-logo": "https://logo.doube.eu.org/博斯高球1.png", "group-title": "", "name": "博斯高球1", "pid": "litv-longturn05,5,2"}, {"tvg-id": "litv-longturn06", "tvg-name": "博斯高球2", "tvg-logo": "https://logo.doube.eu.org/博斯高球2.png", "group-title": "", "name": "博斯高球2", "pid": "litv-longturn06,5,2"}, {"tvg-id": "litv-longturn07", "tvg-name": "博斯运动1", "tvg-logo": "https://logo.doube.eu.org/博斯运动1.png", "group-title": "", "name": "博斯运动1", "pid": "litv-longturn07,5,2"}, {"tvg-id": "litv-longturn08", "tvg-name": "博斯运动2", "tvg-logo": "https://logo.doube.eu.org/博斯运动2.png", "group-title": "", "name": "博斯运动2", "pid": "litv-longturn08,5,2"}, {"tvg-id": "litv-longturn09", "tvg-name": "博斯网球1", "tvg-logo": "https://logo.doube.eu.org/博斯网球1.png", "group-title": "", "name": "博斯网球", "pid": "litv-longturn09,5,2"}, {"tvg-id": "litv-longturn10", "tvg-name": "博斯无限1", "tvg-logo": "https://logo.doube.eu.org/博斯无限1.png", "group-title": "", "name": "博斯无限", "pid": "litv-longturn10,5,2"}, {"tvg-id": "litv-longturn13", "tvg-name": "博斯无限2", "tvg-logo": "https://logo.doube.eu.org/博斯无限2.png", "group-title": "", "name": "博斯无限2", "pid": "litv-longturn13,4,2"}, {"tvg-id": "4gtv-4gtv040", "tvg-name": "中视", "tvg-logo": "https://logo.doube.eu.org/中视.png", "group-title": "", "name": "中视", "pid": "4gtv-4gtv040,1,6"}, {"tvg-id": "4gtv-4gtv064", "tvg-name": "中视菁采台", "tvg-logo": "https://logo.doube.eu.org/中视菁采台.png", "group-title": "", "name": "中视菁采", "pid": "4gtv-4gtv064,1,8"}, {"tvg-id": "4gtv-4gtv074", "tvg-name": "中视新闻台", "tvg-logo": "https://logo.doube.eu.org/中视新闻台.png", "group-title": "", "name": "中视新闻", "pid": "4gtv-4gtv074,1,2"}, {"tvg-id": "4gtv-4gtv080", "tvg-name": "中视经典台", "tvg-logo": "https://logo.doube.eu.org/中视经典台.png", "group-title": "", "name": "中视经典", "pid": "4gtv-4gtv080,1,6"}, {"tvg-id": "4gtv-4gtv006", "tvg-name": "猪哥亮歌厅秀", "tvg-logo": "https://logo.doube.eu.org/猪哥亮歌厅秀.png", "group-title": "", "name": "猪哥亮歌厅秀", "pid": "4gtv-4gtv006,1,9"}, {"tvg-id": "4gtv-4gtv009", "tvg-name": "中天新闻", "tvg-logo": "https://logo.doube.eu.org/中天新闻.png", "group-title": "", "name": "中天新闻", "pid": "4gtv-4gtv009,2,7"}, {"tvg-id": "4gtv-4gtv109", "tvg-name": "中天亚洲", "tvg-logo": "https://logo.doube.eu.org/中天亚洲.png", "group-title": "", "name": "中天亚洲台", "pid": "4gtv-4gtv109,1,7"}, {"tvg-id": "4gtv-4gtv010", "tvg-name": "非凡新闻", "tvg-logo": "https://logo.doube.eu.org/非凡新闻.png", "group-title": "", "name": "非凡新闻", "pid": "4gtv-4gtv010,1,6"}, {"tvg-id": "4gtv-4gtv048", "tvg-name": "非凡商业", "tvg-logo": "https://logo.doube.eu.org/非凡商业.png", "group-title": "", "name": "非凡商业", "pid": "4gtv-4gtv048,1,2"}, {"tvg-id": "litv-longturn14", "tvg-name": "寰宇新闻台", "tvg-logo": "https://logo.doube.eu.org/寰宇新闻台.png", "group-title": "", "name": "寰宇新闻台", "pid": "litv-longturn14,1,2"}, {"tvg-id": "litv-longturn15", "tvg-name": "寰宇新闻台湾台", "tvg-logo": "https://logo.doube.eu.org/寰宇新闻台湾台.png", "group-title": "", "name": "寰宇新闻台湾台", "pid": "4gtv-4gtv156,1,6"}, {"tvg-id": "4gtv-4gtv034", "tvg-name": "八大精彩", "tvg-logo": "https://logo.doube.eu.org/八大精彩.png", "group-title": "", "name": "八大精彩台", "pid": "4gtv-4gtv034,1,6"}, {"tvg-id": "4gtv-4gtv039", "tvg-name": "八大综艺", "tvg-logo": "https://logo.doube.eu.org/八大综艺.png", "group-title": "", "name": "八大综艺台", "pid": "4gtv-4gtv039,1,7"}, {"tvg-id": "4gtv-4gtv084", "tvg-name": "国会频道1", "tvg-logo": "https://logo.doube.eu.org/国会频道1.png", "group-title": "", "name": "国会频道1", "pid": "4gtv-4gtv084,1,6"}, {"tvg-id": "4gtv-4gtv085", "tvg-name": "国会频道2", "tvg-logo": "https://logo.doube.eu.org/国会频道2.png", "group-title": "", "name": "国会频道2", "pid": "4gtv-4gtv085,1,5"}, {"tvg-id": "litv-ftv16", "tvg-name": "好消息1", "tvg-logo": "https://logo.doube.eu.org/好消息1.png", "group-title": "", "name": "好消息1", "pid": "litv-ftv16,1,2"}, {"tvg-id": "litv-ftv16", "tvg-name": "好消息1", "tvg-logo": "https://logo.doube.eu.org/好消息1.png", "group-title": "", "name": "好消息1", "pid": "litv-ftv16,1,6"}, {"tvg-id": "litv-ftv17", "tvg-name": "好消息2", "tvg-logo": "https://logo.doube.eu.org/好消息2.png", "group-title": "", "name": "好消息2", "pid": "litv-ftv17,1,2"}, {"tvg-id": "litv-ftv17", "tvg-name": "好消息2", "tvg-logo": "https://logo.doube.eu.org/好消息2.png", "group-title": "", "name": "好消息2", "pid": "litv-ftv17,1,6"}, {"tvg-id": "4gtv-4gtv045", "tvg-name": "靖洋戏剧台", "tvg-logo": "https://logo.doube.eu.org/靖洋戏剧台.png", "group-title": "", "name": "靖洋戏剧台", "pid": "4gtv-4gtv045,1,6"}, {"tvg-id": "4gtv-4gtv057", "tvg-name": "靖洋卡通台", "tvg-logo": "https://logo.doube.eu.org/靖洋卡通台.png", "group-title": "", "name": "靖洋卡通台", "pid": "4gtv-4gtv057,1,8"}, {"tvg-id": "4gtv-4gtv152", "tvg-name": "东森新闻台", "tvg-logo": "https://logo.doube.eu.org/东森新闻台.png", "group-title": "", "name": "东森新闻", "pid": "4gtv-4gtv152,1,6"}, {"tvg-id": "4gtv-4gtv153", "tvg-name": "东森财经新闻台", "tvg-logo": "https://logo.doube.eu.org/东森财经新闻台.png", "group-title": "", "name": "东森财经新闻", "pid": "4gtv-4gtv153,1,2"}, {"tvg-id": "4gtv-4gtv153", "tvg-name": "东森财经新闻台", "tvg-logo": "https://logo.doube.eu.org/东森财经新闻台.png", "group-title": "", "name": "东森财经新闻", "pid": "4gtv-4gtv153,1,6"}, {"tvg-id": "4gtv-4gtv011", "tvg-name": "影迷數位電影台", "tvg-logo": "https://logo.doube.eu.org/影迷數位電影台.png", "group-title": "", "name": "影迷數位電影台", "pid": "4gtv-4gtv011,1,6"}, {"tvg-id": "4gtv-4gtv013", "tvg-name": "视纳华仁纪实", "tvg-logo": "https://logo.doube.eu.org/视纳华仁纪实.png", "group-title": "", "name": "視納華仁紀實頻道", "pid": "4gtv-4gtv013,1,6"}, {"tvg-id": "4gtv-4gtv014", "tvg-name": "时尚运动X", "tvg-logo": "https://logo.doube.eu.org/时尚运动X.png", "group-title": "", "name": "时尚运动X", "pid": "4gtv-4gtv014,1,5"}, {"tvg-id": "4gtv-4gtv016", "tvg-name": "Globetrotter", "tvg-logo": "https://logo.doube.eu.org/Globetrotter.png", "group-title": "", "name": "GLOBETROTTER", "pid": "4gtv-4gtv016,1,6"}, {"tvg-id": "4gtv-4gtv017", "tvg-name": "amc电影台", "tvg-logo": "https://logo.doube.eu.org/amc电影台.png", "group-title": "", "name": "amc电影台", "pid": "4gtv-4gtv017,1,6"}, {"tvg-id": "4gtv-4gtv018", "tvg-name": "达文西频道", "tvg-logo": "https://logo.doube.eu.org/达文西频道.png", "group-title": "", "name": "达文西频道", "pid": "4gtv-4gtv018,1,6"}, {"tvg-id": "4gtv-4gtv041", "tvg-name": "华视", "tvg-logo": "https://logo.doube.eu.org/华视.png", "group-title": "", "name": "华视", "pid": "4gtv-4gtv041,1,6"}, {"tvg-id": "4gtv-4gtv042", "tvg-name": "公视戏剧", "tvg-logo": "https://logo.doube.eu.org/公视戏剧.png", "group-title": "", "name": "公视戏剧", "pid": "4gtv-4gtv042,1,6"}, {"tvg-id": "4gtv-4gtv043", "tvg-name": "客家电视台", "tvg-logo": "https://logo.doube.eu.org/客家电视台.png", "group-title": "", "name": "客家电视台", "pid": "4gtv-4gtv043,1,6"}, {"tvg-id": "4gtv-4gtv049", "tvg-name": "采昌影剧台", "tvg-logo": "https://logo.doube.eu.org/采昌影剧台.png", "group-title": "", "name": "采昌影剧", "pid": "4gtv-4gtv049,1,8"}, {"tvg-id": "4gtv-4gtv052", "tvg-name": "华视新闻", "tvg-logo": "https://logo.doube.eu.org/华视新闻.png", "group-title": "", "name": "华视新闻", "pid": "4gtv-4gtv052,1,2"}, {"tvg-id": "4gtv-4gtv053", "tvg-name": "GINXEsportsTV", "tvg-logo": "https://logo.doube.eu.org/GINXEsportsTV.png", "group-title": "", "name": "GinxTV", "pid": "4gtv-4gtv053,1,8"}, {"tvg-id": "4gtv-4gtv059", "tvg-name": "CLASSICA古典乐", "tvg-logo": "https://logo.doube.eu.org/CLASSICA古典乐.png", "group-title": "", "name": "古典音乐台", "pid": "4gtv-4gtv059,1,6"}, {"tvg-id": "4gtv-4gtv070", "tvg-name": "ELTV娱乐", "tvg-logo": "https://logo.doube.eu.org/ELTV娱乐.png", "group-title": "", "name": "爱尔达娱乐", "pid": "4gtv-4gtv070,1,7"}, {"tvg-id": "4gtv-4gtv075", "tvg-name": "镜电视新闻台", "tvg-logo": "https://logo.doube.eu.org/镜电视新闻台.png", "group-title": "", "name": "镜新闻", "pid": "4gtv-4gtv075,1,2"}, {"tvg-id": "4gtv-4gtv077", "tvg-name": "TraceSportStars", "tvg-logo": "https://logo.doube.eu.org/TraceSportStars.png", "group-title": "", "name": "TRACE SPORTS STARS", "pid": "4gtv-4gtv077,1,2"}, {"tvg-id": "4gtv-4gtv079", "tvg-name": "ARIRANG", "tvg-logo": "https://logo.doube.eu.org/ARIRANG.png", "group-title": "", "name": "阿里郎", "pid": "4gtv-4gtv079,1,2"}, {"tvg-id": "4gtv-4gtv082", "tvg-name": "TraceUrban", "tvg-logo": "https://logo.doube.eu.org/TraceUrban.png", "group-title": "", "name": "TRACE URBAN", "pid": "4gtv-4gtv082,1,6"}, {"tvg-id": "4gtv-4gtv083", "tvg-name": "MezzoLiveHD", "tvg-logo": "https://logo.doube.eu.org/MezzoLiveHD.png", "group-title": "", "name": "MEZZO LIVE", "pid": "4gtv-4gtv083,1,6"}, {"tvg-id": "4gtv-4gtv101", "tvg-name": "智林体育台", "tvg-logo": "https://logo.doube.eu.org/智林体育台.png", "group-title": "", "name": "智林体育台", "pid": "4gtv-4gtv101,1,5"}, {"tvg-id": "4gtv-4gtv101", "tvg-name": "智林体育台", "tvg-logo": "https://logo.doube.eu.org/智林体育台.png", "group-title": "", "name": "智林体育台", "pid": "4gtv-4gtv101,1,6"}, {"tvg-id": "4gtv-4gtv104", "tvg-name": "第1商业台", "tvg-logo": "https://logo.doube.eu.org/第1商业台.png", "group-title": "", "name": "第1商业台", "pid": "4gtv-4gtv104,1,7"}, {"tvg-id": "litv-ftv03", "tvg-name": "美国之音", "tvg-logo": "https://logo.doube.eu.org/美国之音.png", "group-title": "", "name": "美国之音", "pid": "litv-ftv03,1,7"}, {"tvg-id": "litv-ftv10", "tvg-name": "半岛国际新闻", "tvg-logo": "https://logo.doube.eu.org/半岛国际新闻.png", "group-title": "", "name": "半岛新闻", "pid": "litv-ftv10,1,7"}, {"tvg-id": "litv-ftv15", "tvg-name": "影迷纪实台", "tvg-logo": "https://logo.doube.eu.org/影迷纪实台.png", "group-title": "", "name": "影迷纪实台", "pid": "litv-ftv15,1,7"}, {"tvg-id": "4gtv-4gtv076", "tvg-name": "亚洲旅游台", "tvg-logo": "https://logo.doube.eu.org/亚洲旅游台.png", "group-title": "", "name": "亚洲旅游台", "pid": "4gtv-4gtv076,1,2"}, {"tvg-id": "litv-longturn19", "tvg-name": "Smart知识台", "tvg-logo": "https://logo.doube.eu.org/Smart知识台.png", "group-title": "", "name": "Smart知识台", "pid": "litv-longturn19,5,6"}, {"tvg-id": "litv-longturn20", "tvg-name": "ELTV生活英语台", "tvg-logo": "https://logo.doube.eu.org/ELTV生活英语台.png", "group-title": "", "name": "生活英语台", "pid": "litv-longturn20,5,6"}]

app = FastAPI()
spider = Spider()


@app.get("/live", response_class=PlainTextResponse, tags=["Playlist"])
async def master_playlist(request: Request):
    return spider.channel_master_playlist(request)


@app.get("/proxy", tags=["Proxy"])
async def proxy(
    request: Request,
    type: str,
    pid: Optional[str] = None,
    url: Optional[str] = None,
):
    if type == "m3u8" and pid:
        body = spider.build_segment_playlist(pid)
        return PlainTextResponse(
            body, media_type="application/vnd.apple.mpegurl; charset=utf-8"
        )

    if type == "ts" and url:
        return StreamingResponse(
            spider.fetch_ts_stream(url), media_type="video/mp2t"
        )

    raise HTTPException(status_code=400, detail="Missing or wrong parameters")


@app.get("/", include_in_schema=False)
def _root() -> Response:
    return Response(
        '<meta http-equiv="refresh" content="0;url=/docs">', media_type="text/html"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info"
    )
