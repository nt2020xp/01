import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import cloudscraper
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import urllib.parse
from dotenv import load_dotenv
from datetime import timedelta
import logging
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import asyncio as aioredis

# 載入環境變數
load_dotenv()

# 初始化 FastAPI
app = FastAPI(title="4GTV Proxy Service")

# 強制 HTTPS (生產環境建議開啟)
# app.add_middleware(HTTPSRedirectMiddleware)

# 日誌配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("4gtv_proxy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 從環境變數獲取金鑰
AES_KEY = os.getenv("AES_KEY", "ilyB29ZdruuQjC45JhBBR7o2Z8WJ26Vg").encode()
AES_IV = os.getenv("AES_IV", "JUMxvVMmszqUTeKn").encode()

# Redis 快取配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))  # 預設 5 分鐘

@app.on_event("startup")
async def startup():
    # 初始化速率限制
    redis = aioredis.from_url(REDIS_URL)
    await FastAPILimiter.init(redis)

def encrypt_data(data: str, key: bytes, iv: bytes) -> str:
    """AES-256-CBC 加密"""
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(data.encode(), AES.block_size)
        return base64.b64encode(cipher.encrypt(padded_data)).decode()
    except Exception as e:
        logger.error(f"加密失敗: {str(e)}")
        raise ValueError("資料加密錯誤")

def decrypt_data(encrypted_data: str, key: bytes, iv: bytes) -> str:
    """AES-256-CBC 解密"""
    try:
        decipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = unpad(
            decipher.decrypt(base64.b64decode(encrypted_data)),
            AES.block_size
        )
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"解密失敗: {str(e)}")
        raise ValueError("資料解密錯誤")

async def fetch_channel_data(channel_id: str) -> dict:
    """從 4GTV API 獲取頻道資料"""
    scraper = cloudscraper.create_scraper()
    try:
        # 驗證 channel_id 是否為數字
        if not channel_id.isdigit():
            raise ValueError("無效的頻道 ID")

        url = f"https://api2.4gtv.tv/Channel/GetChannel/{channel_id}"
        response = scraper.get(url, timeout=10)
        response.raise_for_status()
        return json.loads(response.text)["Data"]
    except Exception as e:
        logger.error(f"獲取頻道資料失敗: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail="頻道不存在或獲取資料失敗"
        )

async def get_stream_url(channel_data: dict) -> str:
    """獲取串流網址"""
    scraper = cloudscraper.create_scraper()
    try:
        jarray = {
            "fnCHANNEL_ID": channel_data["fnID"],
            "fsASSET_ID": channel_data["fs4GTV_ID"],
            "fsDEVICE_TYPE": "mobile",
            "clsIDENTITY_VALIDATE_ARUS": {"fsVALUE": ""}
        }
        encrypted_data = encrypt_data(json.dumps(jarray), AES_KEY, AES_IV)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = "value=" + urllib.parse.quote_plus(encrypted_data)

        response = scraper.post(
            "https://api2.4gtv.tv//Channel/GetChannelUrl3",
            data=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()

        decrypted_data = decrypt_data(
            json.loads(response.text)["Data"],
            AES_KEY,
            AES_IV
        )
        return json.loads(decrypted_data)["flstURLs"][0]
    except Exception as e:
        logger.error(f"獲取串流網址失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="無法取得串流網址"
        )

@app.get("/4gtv/{channel_id}",
         dependencies=[RateLimiter(times=30, seconds=60)],
         summary="取得 4GTV 頻道串流網址",
         response_description="302 重新導向至串流")
async def get_playlist(
    channel_id: str,
    request: Request
):
    """
    通過 4GTV 頻道 ID 獲取串流網址並重新導向
    
    - **channel_id**: 4GTV 頻道 ID (數字)
    - 返回: 302 重新導向至實際串流
    """
    try:
        # 檢查快取
        redis = aioredis.from_url(REDIS_URL)
        cache_key = f"4gtv:{channel_id}"
        cached_url = await redis.get(cache_key)
        
        if cached_url:
            logger.info(f"從快取返回頻道 {channel_id}")
            return RedirectResponse(url=cached_url.decode())

        # 獲取頻道資料
        channel_data = await fetch_channel_data(channel_id)
        
        # 獲取串流網址
        stream_url = await get_stream_url(channel_data)
        
        # 存入快取
        await redis.setex(cache_key, timedelta(seconds=CACHE_TTL), stream_url)
        logger.info(f"成功獲取頻道 {channel_id} 串流網址")
        
        return RedirectResponse(url=stream_url, status_code=302)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="伺服器內部錯誤"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        ssl_keyfile=os.getenv("SSL_KEYFILE"),
        ssl_certfile=os.getenv("SSL_CERTFILE")
    )
