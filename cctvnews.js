const crypto = require('crypto');
const axios = require('axios');
const express = require('express');
const app = express();
const port = 3000;

const CHANNEL_MAP = {
    'cctv1': '11200132825562653886',
    'cctv2': '12030532124776958103',
    'cctv4': '10620168294224708952',
    'cctv7': '8516529981177953694',
    'cctv9': '7252237247689203957',
    'cctv10': '14589146016461298119',
    'cctv12': '13180385922471124325',
    'cctv13': '16265686808730585228',
    'cctv17': '4496917190172866934',
    'cctv4k': '2127841942201075403'
};

async function getCCTVUrl(id) {
    const articleId = CHANNEL_MAP[id];
    if (!articleId) return null;

    const t = Math.floor(Date.now() / 1000);
    const tStr = t.toString();
    
    // 1. MD5 簽名 sail
    const sail = crypto.createHash('md5').update(`articleId=${articleId}&scene_type=6`).digest('hex');
    
    // 2. EMAS Gateway 簽名
    const w = `&&&20000009&${sail}&${tStr}&emas.feed.article.live.detail&1.0.0&&&&&`;
    const sign = crypto.createHmac('sha256', 'emasgatewayh5').update(w).digest('hex');

    const apiUrl = `emas-api.cctvnews.cctv.com{articleId}&scene_type=6`;
    const client_id = crypto.createHash('md5').update(tStr).digest('hex');

    const headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'cookieuid': client_id,
        'from-client': 'h5',
        'referer': 'm-live.cctvnews.cctv.com',
        'x-emas-gw-appkey': '20000009',
        'x-emas-gw-sign': sign,
        'x-emas-gw-t': tStr,
        'x-req-ts': (t * 1000).toString()
    };

    try {
        const response = await axios.get(apiUrl, { headers, timeout: 5000 });
        const resData = response.data;
        
        // 3. 解碼 Base64 響應
        const decodedData = JSON.parse(Buffer.from(resData.response, 'base64').toString());
        const data = decodedData.data;
        
        // 4. 提取加密連結與密鑰
        const authUrl = data.live_room.liveCameraList[0].pullUrlList[0].authResultUrl[0].authUrl;
        const dk = data.dk;
        
        const key = dk.substring(0, 8) + tStr.substring(tStr.length - 8);
        const iv = dk.substring(dk.length - 8) + tStr.substring(0, 8);

        // 5. AES-128-CBC 解密
        const decipher = crypto.createDecipheriv('aes-128-cbc', Buffer.from(key), Buffer.from(iv));
        let decrypted = decipher.update(authUrl, 'base64', 'utf8');
        decrypted += decipher.final('utf8');

        return decrypted;
    } catch (e) {
        console.error(`[${id}] 獲取失敗:`, e.message);
        return null;
    }
}

// 建立 HTTP 服務
app.get('/live/:id', async (req, res) => {
    const finalUrl = await getCCTVUrl(req.params.id);
    if (finalUrl) {
        // 使用 302 重定向，讓播放器每次都獲取最新 Token
        res.redirect(302, finalUrl);
    } else {
        res.status(404).send('頻道不存在或抓取失敗');
    }
});

app.listen(port, () => {
    console.log(`CCTV 直播服務已啟動：http://localhost:${port}/live/cctv1`);
    console.log(`可用頻道: ${Object.keys(CHANNEL_MAP).join(', ')}`);
});
