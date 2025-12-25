<?php
error_reporting(E_ALL & ~E_NOTICE);
ini_set('display_errors', 0); 
// 允许跨域，解决部分Web播放器和特定客户端的问题
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, OPTIONS');
header('Content-Type: text/plain; charset=utf-8');
date_default_timezone_set("Asia/Shanghai");

// 核心配置
const CONFIG = [
    'upstream'   => ['http://66.90.99.154:8278/'],
    'list_url'   => 'https://cdn.jsdelivr.net/gh/hostemail/cdn@main/data/smart.txt',
    'backup_url' => 'https://cdn.jsdelivr.net/gh/hostemail/cdn@main/data/smart1.txt', 
    'token_ttl'  => 2400,  
    'cache_ttl'  => 3600, 
    'fallback'   => '', // 留空，出错直接报 HTTP 错误
    'clear_key'  => 'leifeng'
];

function getUpstream() {
    static $index = 0;
    $upstreams = CONFIG['upstream'];
    $current = $upstreams[$index % count($upstreams)];
    $index++;
    return $current;
}

try {
    if (isset($_GET['action']) && $_GET['action'] === 'clear_cache') {
        clearCache();
    } elseif (!isset($_GET['id'])) {
        sendTXTList();
    } else {
        handleChannelRequest();
    }
} catch (Exception $e) {
    header('HTTP/1.1 503 Service Unavailable');
    exit("System Error");
}

// --- 核心功能函数 ---

function sendTXTList() {
    header("Cache-Control: no-store, no-cache, must-revalidate");
    try {
        $channels = getChannelList();
    } catch (Exception $e) {
        exit("List Error");
    }
    $baseUrl  = getBaseUrl();
    $script   = basename(__FILE__);
    $grouped = [];
    foreach ($channels as $chan) {
        $grouped[$chan['group']][] = $chan;
    }
    $output = '';
    foreach ($grouped as $group => $items) {
        $output .= htmlspecialchars($group) . ",#genre#\n";
        foreach ($items as $chan) {
            $output .= sprintf("%s,%s/%s?id=%s\n",
                htmlspecialchars($chan['name']),
                $baseUrl,
                $script,
                urlencode($chan['id'])
            );
        }
        $output .= "\n";
    }
    header('Content-Disposition: inline; filename="channels.txt"');
    echo trim($output);
}

function handleChannelRequest() {
    $channelId = $_GET['id'];
    $tsFile    = $_GET['ts'] ?? '';
    
    // 获取Token，如果是TS请求，不进行跳转逻辑，只做验证
    $token = manageToken(!empty($tsFile)); 

    if ($tsFile) {
        proxyTS($channelId, $tsFile);
    } else {
        generateM3U8($channelId, $token);
    }
}

// Token管理：isTsRequest为true时，绝对不输出 Location 跳转
function manageToken($isTsRequest = false) {
    $token = $_GET['token'] ?? '';
    $isValid = false;
    
    if (!empty($token)) {
        $parts = explode(':', $token);
        if (count($parts) === 2) {
            $timestamp = (int)$parts[1];
            // 只要格式对，稍微放宽一点时间限制给播放器缓冲用
            if ((time() - $timestamp) <= (CONFIG['token_ttl'] + 300)) {
                $isValid = true;
            }
        }
    }
    
    if ($isValid) {
        return $token;
    }
    
    // 如果Token无效
    if ($isTsRequest) {
        // 播放器正在请求TS，严禁跳转，如果Token失效，最好也放行（或者返回403）
        // 这里为了稳定性，选择放行（即便Token过期也让他看完这个切片），防止卡顿
        return $token; 
    }
    
    // 如果是请求M3U8，Token无效则重定向生成新的
    $newToken = bin2hex(random_bytes(16)) . ':' . time();
    // 这里不需要重定向逻辑，因为generateM3U8会把newToken写进去
    // 之前的代码在这里做了多余的跳转，导致逻辑复杂
    return $newToken;
}

function generateM3U8($channelId, $token) {
    $upstream = getUpstream();
    $authUrl = $upstream . "$channelId/playlist.m3u8?" . http_build_query([
        'tid'  => 'mc42afe745533',
        'ct'   => intval(time() / 150),
        'tsum' => md5("tvata nginx auth module/$channelId/playlist.m3u8mc42afe745533" . intval(time() / 150))
    ]);
    
    $content = fetchUrl($authUrl); // 使用带Header的fetchUrl
    
    if (!$content || strpos($content, 'EXTM3U') === false) {
        header('HTTP/1.1 404 Not Found');
        exit("Stream Not Found");
    }
    
    $baseUrl = getBaseUrl() . '/' . basename(__FILE__);
    $content = preg_replace_callback('/(\S+\.ts)/', function($m) use ($baseUrl, $channelId, $token) {
        return "$baseUrl?id=" . urlencode($channelId) . "&ts=" . urlencode($m[1]) . "&token=" . urlencode($token);
    }, $content);
    
    header('Content-Type: application/vnd.apple.mpegurl');
    header('Content-Disposition: inline; filename="playlist.m3u8"');
    echo $content;
}

// [针对播放器优化] 代理TS流
function proxyTS($channelId, $tsFile) {
    $upstream = getUpstream();
    $url = $upstream . "$channelId/$tsFile";
    
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true, // 改回true，存入变量，为了计算Content-Length
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER     => [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "CLIENT-IP: 127.0.0.1",      
            "X-FORWARDED-FOR: 127.0.0.1" 
        ]
    ]);

    $data = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode != 200 || empty($data)) {
        header('HTTP/1.1 404 Not Found');
        exit;
    }

    // 核心修复：发送 Content-Length
    // 播放器看到这个才会认为这是一个正常的视频文件
    header('Content-Type: video/MP2T');
    header('Content-Length: ' . strlen($data)); 
    header('Connection: keep-alive');
    echo $data;
    exit;
}

// 通用抓取
function fetchUrl($url) {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT        => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPHEADER     => [
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "CLIENT-IP: 127.0.0.1",      
            "X-FORWARDED-FOR: 127.0.0.1" 
        ]
    ]);
    $data = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return $code == 200 ? $data : null;
}

function getBaseUrl() {
    if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && $_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https') {
        $protocol = 'https';
    } elseif (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on') {
        $protocol = 'https';
    } else {
        $protocol = 'http';
    }
    $host = $_SERVER['HTTP_HOST'];
    return $protocol . "://" . $host;
}

function getChannelList() {
    if (extension_loaded('apcu')) {
        $cached = apcu_fetch('smart_channels');
        if ($cached) return $cached;
    }
    // 简单重试逻辑
    $raw = fetchUrl(CONFIG['list_url']);
    if (!$raw) $raw = fetchUrl(CONFIG['backup_url']);
    if (!$raw) throw new Exception("Load Error");

    $list = [];
    $currentGroup = '默认分组';
    foreach (explode("\n", trim($raw)) as $line) {
        $line = trim($line);
        if (!$line) continue;
        if (strpos($line, '#genre#') !== false) {
            $currentGroup = trim(str_replace(',#genre#', '', $line));
            continue;
        }
        if (preg_match('/[?&]id=([^&]+)/', $line, $m) || preg_match('/\/\/:id=(\w+)/', $line, $m)) {
             $list[] = [
                'id'    => $m[1],
                'name'  => trim(explode(',', $line)[0]),
                'group' => $currentGroup
            ];
        }
    }
    if (extension_loaded('apcu') && !empty($list)) {
        apcu_store('smart_channels', $list, CONFIG['cache_ttl']);
    }
    return $list;
}

function clearCache() {
    $validKey = $_GET['key'] ?? '';
    if (!hash_equals(CONFIG['clear_key'], $validKey)) exit("403");
    if (extension_loaded('apcu')) apcu_clear_cache();
    exit("Cache Cleared");
}
?>
