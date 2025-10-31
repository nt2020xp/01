<?php
// --------------------------------------------------------------------------------
// 為了在 PHP 中模擬 Python 的繼承和方法，我們定義一個主類。
// 實際應用中，您可能需要繼承自您項目中的 Spider 基類。
// --------------------------------------------------------------------------------

class MyTaiwanSpider {

    // 模擬 Spider 基類的屬性
    protected $proxy = null;
    protected $is_proxy = false;
    protected $subscription_url = "http://141.11.87.241:20013/?type=m3u";
    protected $refresh_interval = 5; // 控制刷新间隔（单位：秒）
    protected $extendDict = [];

    // 相当于 Python 的 __init__ 或 setup 方法
    public function init($extend = null) {
        if ($extend) {
            // 模拟 json.loads(extend)
            $extendData = json_decode($extend, true);
            if (json_last_error() === JSON_ERROR_NONE && is_array($extendData)) {
                $this->extendDict = $extendData;
                
                $this->proxy = $this->extendDict['proxy'] ?? null;
                $this->is_proxy = $this->proxy !== null;
                
                // 支持从extend动态调整刷新间隔
                if (isset($this->extendDict["refresh_interval"])) {
                    $interval = (int)$this->extendDict["refresh_interval"];
                    if ($interval > 0) {
                        $this->refresh_interval = $interval;
                        echo "已加载自定义刷新间隔：{$this->refresh_interval}秒\n";
                    }
                }
                
                // 支持动态覆盖订阅链接
                if (isset($this->extendDict["subscription_url"])) {
                    $this->subscription_url = $this->extendDict["subscription_url"];
                    echo "已加载自定义订阅链接：{$this->subscription_url}\n";
                }

                if ($this->is_proxy) {
                    // 仅打印代理的键（模拟 list(self.proxy.keys())）
                    echo "已启用代理：" . print_r(array_keys((array)$this->proxy), true) . "\n";
                }
            } else {
                echo "extend参数解析错误或格式不正确，使用默认配置\n";
            }
        }
    }

    // 相当于 Python 的 getName
    public function getName() {
        return "台湾4g备用(php10175)";
    }

    // 相当于 Python 的 isVideoFormat
    public function isVideoFormat($url) {
        return true;
    }

    // 相当于 Python 的 manualVideoCheck
    public function manualVideoCheck() {
        return true;
    }

    // 相当于 Python 的 b64encode
    public function b64encode($data) {
        return base64_encode($data);
    }

    // 相当于 Python 的 b64decode
    public function b64decode($data) {
        // PHP 的 base64_decode 默认返回二进制数据，这里需要解码成 UTF-8 字符串
        return base64_decode($data); 
    }

    /**
     * 核心逻辑：订阅失败不返回应急频道，循环刷新重试
     * @param string $url 占位符，实际未使用
     * @return string M3U 内容或抛出异常（在真实框架中可能需要返回特定格式）
     */
    public function liveContent($url) {
        $headers = [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept: */*",
            "Accept-Language: zh-CN,zh;q=0.9",
            "Connection: close",  // 禁用长连接，适配不稳定服务器
            "Cache-Control: no-cache",
            "Pragma: no-cache"
        ];

        $retry_count = 1; // 计数

        while (true) { // 无限循环，直到请求成功
            echo "【订阅刷新】第{$retry_count}次尝试，订阅链接：{$this->subscription_url}\n";
            
            // 使用 cURL 模拟 requests.get
            $ch = curl_init();
            curl_setopt($ch, CURLOPT_URL, $this->subscription_url);
            curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true); // 返回响应而不是直接输出
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true); // 允许重定向
            curl_setopt($ch, CURLOPT_HEADER, false); // 不返回响应头
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false); // 忽略 SSL 证书验证 (对应 verify=False)
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5); // 连接超时 5秒 (对应 timeout[0])
            curl_setopt($ch, CURLOPT_TIMEOUT, 25); // 读取超时 25秒 (略大于 Python 的 20)

            // 代理设置
            if ($this->is_proxy && is_array($this->proxy)) {
                if (isset($this->proxy['http'])) {
                    curl_setopt($ch, CURLOPT_PROXY, $this->proxy['http']);
                } elseif (isset($this->proxy['https'])) { // 简单处理，实际需根据 URL 协议切换
                    curl_setopt($ch, CURLOPT_PROXY, $this->proxy['https']);
                }
            }

            $response_content = curl_exec($ch);
            $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

            if (curl_errno($ch)) {
                $error = curl_error($ch);
                curl_close($ch);
                // cURL 错误通常是连接或超时问题
                $e = new \Exception("cURL Error: " . $error);
            } else {
                curl_close($ch);
                
                // 检查 HTTP 状态码 (对应 response.raise_for_status())
                if ($status_code >= 200 && $status_code < 300) {
                    // 请求成功
                    $m3u_content = trim($response_content);
                    // 统计 #EXTINF 数量
                    $channel_count = substr_count($m3u_content, "#EXTINF");
                    echo "【响应状态】第{$retry_count}次：状态码{$status_code}\n";
                    echo "【刷新成功】第{$retry_count}次尝试成功，获取{$channel_count}个频道\n";
                    return $m3u_content;
                } else {
                    // HTTP 状态码非 2xx
                    $e = new \Exception("HTTP Status Code Error: {$status_code}");
                }
            }

            // 如果代码执行到这里，说明发生了异常（网络错误或非 2xx 状态码）
            if (isset($e)) {
                $error_msg = "【刷新失败】第{$retry_count}次：Exception - " . $e->getMessage();
                echo "{$error_msg}，{$this->refresh_interval}秒后重新尝试\n";
                $retry_count++;
                sleep($this->refresh_interval); // 等待后继续循环重试
            }
        }
    }

    // 影视壳必需空接口（保持不变）
    public function homeContent($filter) {
        return ["class" => [], "list" => []];
    }
    public function homeVideoContent() {
        return ["list" => []];
    }
    public function categoryContent($cid, $page, $filter, $ext) {
        return ["list" => [], "page" => $page, "pagecount" => 1, "total" => 0];
    }
    public function detailContent($did) {
        return [];
    }
    public function searchContent($key, $quick, $page='1') {
        return ["list" => [], "page" => $page, "pagecount" => 1, "total" => 0];
    }
    public function searchContentPage($keywords, $quick, $page) {
        return $this->searchContent($keywords, $quick, $page);
    }

    public function playerContent($flag, $pid, $vipFlags) {
        return ["parse" => 0, "playUrl" => "", "header" => []];
    }

    public function localProxy($params) {
        if (isset($params['type']) && in_array($params['type'], ["mpd", "ts"]) && isset($params['url'])) {
            try {
                $url = $this->b64decode($params['url']);
                $headers = [
                    'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 
                    "Connection: close"
                ];

                // 使用 cURL 进行代理转发
                $ch = curl_init();
                curl_setopt($ch, CURLOPT_URL, $url);
                curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                curl_setopt($ch, CURLOPT_HEADER, true); // 需要返回头部以获取 Content-Type
                curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false); 
                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
                curl_setopt($ch, CURLOPT_TIMEOUT, 30);
                curl_setopt($ch, CURLOPT_BINARYTRANSFER, true); // 二进制数据传输

                // 代理设置
                if ($this->is_proxy && is_array($this->proxy)) {
                    if (isset($this->proxy['http'])) {
                        curl_setopt($ch, CURLOPT_PROXY, $this->proxy['http']);
                    } elseif (isset($this->proxy['https'])) {
                        curl_setopt($ch, CURLOPT_PROXY, $this->proxy['https']);
                    }
                }

                $response = curl_exec($ch);
                $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                
                if (curl_errno($ch)) {
                    throw new \Exception("Proxy cURL Error: " . curl_error($ch));
                }
                curl_close($ch);

                if ($status_code == 200) {
                    // 解析头和内容
                    list($header_str, $body) = explode("\r\n\r\n", $response, 2);
                    $headers_array = [];
                    foreach (explode("\r\n", $header_str) as $line) {
                        if (strpos($line, ':') !== false) {
                            list($key, $value) = explode(':', $line, 2);
                            $headers_array[trim($key)] = trim($value);
                        }
                    }

                    $contentType = $headers_array['Content-Type'] ?? 'application/octet-stream';
                    // 返回格式 [200, Content-Type, content, headers_map]
                    return [200, $contentType, $body, $headers_array]; 
                } else {
                    throw new \Exception("Proxy request failed with status: {$status_code}");
                }

            } catch (\Exception $e) {
                echo "代理转发失败：" . $e->getMessage() . "\n";
            }
        }
        // 失败或类型不匹配，返回默认重定向
        return [302, "text/plain", null, ['Location' => 'https://sf1-cdn-tos.huoshanstatic.com/obj/media-fe/xgplayer_doc_video/mp4/xgplayer-demo-720p.mp4']];
    }
}

// --------------------------------------------------------------------------------
// 本地测试逻辑（运行脚本验证循环刷新效果）
// --------------------------------------------------------------------------------
echo "=== 台湾4g备用爬虫 本地测试（循环刷新模式）===\n";
$spider = new MyTaiwanSpider();

// 测试时可通过extend调整刷新间隔（示例：3秒刷新一次）
// $test_extend = '{"refresh_interval":3, "proxy":{"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}}';
$test_extend = "{}";
$spider->init($test_extend);

try {
    // 调用liveContent，会一直循环直到订阅成功
    $content = $spider->liveContent("test");
    echo "\n=== 测试成功 ===\n";
    $channel_count = substr_count($content, "#EXTINF");
    echo "频道数量：{$channel_count} 个\n";
    echo "前5行内容预览：\n";
    $lines = explode("\n", $content);
    for ($i = 0; $i < 5 && $i < count($lines); $i++) {
        echo " " . ($i + 1) . ". " . $lines[$i] . "\n";
    }
} catch (Exception $e) {
    // 在实际框架中，liveContent通常会自己处理无限循环，
    // 只有在外部调用且被中断时才会捕获到异常
    echo "\n=== 测试中断或异常 ===\n";
    echo "错误：" . $e->getMessage() . "\n";
}

?>
