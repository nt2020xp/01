const CryptoJS = require("crypto");

function main(item) {
    // 重试机制
    for (let attempt = 0; attempt < 3; attempt++) {
        try {
            const id = item.id || 'cctv1';
            const n = {
                'cctv1': '11200132825562653886',
                'cctv2': '12030532124776958103',
                'cctv4': '10620168294224708952',
                'cctv7': '8516529981177953694',
                'cctv9': '7252237247689203957',
                'cctv10': '14589146016461298119',
                'cctv12': '13180385922471124325',
                'cctv13': '16265686808730585228',
                'cctv17': '4496917190172866934',
                'cctv4k': '2127841942201075403',
            };
            
            const articleId = n[id];
            if (!articleId) {
                return { 
                    url: null, 
                    error: `不支持的频道ID: ${id}`,
                    success: false 
                };
            }

            const t = Math.floor(Date.now() / 1000);
            const sail = ku9.md5(`articleId=${articleId}&scene_type=6`);
            const w = `&&&20000009&${sail}&${t}&emas.feed.article.live.detail&1.0.0&&&&&`;
            const k = "emasgatewayh5";
            const sign = CryptoJS.HmacSHA256(w, k).toString();
            const url = `https://emas-api.cctvnews.cctv.com/h5/emas.feed.article.live.detail/1.0.0?articleId=${articleId}&scene_type=6`;
            const client_id = ku9.md5(t.toString());
            const headers = {
                'cookieuid': client_id,
                'from-client': 'h5',
                'referer': 'https://m-live.cctvnews.cctv.com/',
                'x-emas-gw-appkey': '20000009',
                'x-emas-gw-pv': '6.1',
                'x-emas-gw-sign': sign,
                'x-emas-gw-t': t,
                'x-req-ts': t * 1000
            };

            const res = ku9.get(url, headers);
            if (!res) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: '网络请求失败',
                    success: false 
                };
            }

            const responseData = JSON.parse(res);
            if (!responseData || !responseData.response) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: 'API返回数据格式错误',
                    success: false 
                };
            }

            const decodedData = JSON.parse(ku9.decodeBase64(responseData.response));
            if (!decodedData || !decodedData.data) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: '解码后的数据格式错误',
                    success: false 
                };
            }

            const data = decodedData.data;
            
            // 使用安全访问函数，避免直接访问可能为null的属性
            const getSafeValue = (obj, path, defaultValue = null) => {
                const keys = path.split('.');
                let result = obj;
                for (const key of keys) {
                    if (result === null || result === undefined) return defaultValue;
                    // 处理数组索引
                    if (key.includes('[') && key.includes(']')) {
                        const arrayKey = key.split('[')[0];
                        const index = parseInt(key.split('[')[1].split(']')[0]);
                        if (!Array.isArray(result[arrayKey]) || index >= result[arrayKey].length) {
                            return defaultValue;
                        }
                        result = result[arrayKey][index];
                    } else {
                        result = result[key];
                    }
                }
                return result === null || result === undefined ? defaultValue : result;
            };
            
            // 安全获取认证URL
            const authUrl = getSafeValue(data, 'live_room.liveCameraList[0].pullUrlList[0].authResultUrl[0].authUrl');
            if (!authUrl) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: '无法获取认证URL，可能该频道当前无直播',
                    success: false 
                };
            }
            
            const dk = getSafeValue(data, 'dk');
            if (!dk) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: '缺少解密密钥(dk)',
                    success: false 
                };
            }

            const key = dk.substring(0, 8) + t.toString().substring(t.toString().length - 8);
            const iv = dk.substring(dk.length - 8) + t.toString().substring(0, 8);
            const decrypted = ku9.opensslDecrypt(authUrl, "AES-128-CBC", key, 0, iv);
            
            if (!decrypted) {
                if (attempt < 2) continue; // 重试
                return { 
                    url: null, 
                    error: 'URL解密失败',
                    success: false 
                };
            }
            
            return { 
                url: decrypted,
                success: true 
            };

        } catch (error) {
            // 最后一次尝试仍然失败，返回错误
            if (attempt === 2) {
                return {
                    url: null,
                    error: `执行错误: ${error.message}`,
                    success: false
                };
            }
            // 否则继续重试
        }
    }
}
