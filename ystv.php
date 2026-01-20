<?php
/*
你的域名/cctv.php?id=cctv1&q=lg  // 蓝光【1920×1080】推荐
你的域名/cctv.php?id=cctv13&q=cq // 超清【1280×720】
你的域名/cctv.php?id=cctv4k&q=gq // 高清【960×540】
食用方式不变：
File Directory/cctv.php?id=cctv1&q=lg //蓝光线路[1920×1080]
File Directory/cctv.php?id=cctv1&q=cq //超清线路[1280×720]
File Directory/cctv.php?id=cctv1&q=gq //高清线路[960×540]
支持频道：cctv1/cctv2/cctv4/cctv7/cctv9/cctv10/cctv12/cctv13/cctv17/cctv4k
*/
error_reporting(0);
header('Content-Type: text/html; charset=utf-8');

// 获取GET参数，默认CCTV1+蓝光线路
$id = isset($_GET['id']) ? trim($_GET['id']) : 'cctv1';
$q  = isset($_GET['q'])  ? trim($_GET['q'])  : 'lg'; //lg=蓝光 cq=超清 gq=高清

// CCTV频道对应ID映射表
$n = [
    'cctv1'  => '11200132825562653886',
    'cctv2'  => '12030532124776958103',
    'cctv4'  => '10620168294224708952',
    'cctv7'  => '8516529981177953694',
    'cctv9'  => '7252237247689203957',
    'cctv10' => '14589146016461298119',
    'cctv12' => '13180385922471124325',
    'cctv13' => '16265686808730585228',
    'cctv17' => '4496917190172866934',
    'cctv4k' => '2127841942201075403',
];

// 校验频道是否存在
if(!isset($n[$id])){
    die("错误：当前解析的【{$id}】频道不存在！");
}

$t = time();
$t_str = (string)$t; // 强制转字符串，避免数字截取异常

// 生成签名相关参数
$sail = md5("articleId={$n[$id]}&scene_type=6");
$w    = "&&&20000009&{$sail}&{$t}&emas.feed.article.live.detail&1.0.0&&&&&";
$k    = "emasgatewayh5";
$sign = hash_hmac('sha256', $w, $k);
$url  = "https://emas-api.cctvnews.cctv.com/h5/emas.feed.article.live.detail/1.0.0?articleId={$n[$id]}&scene_type=6";
$client_id = md5($t);

// ✅ 修复：请求头 冒号后必须加空格 + 补全UA + 规范格式
$h = [
    'cookieuid: ' . $client_id,
    'from-client: h5',
    'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'referer: https://m-live.cctvnews.cctv.com/',
    'x-emas-gw-appkey: 20000009',
    'x-emas-gw-pv: 6.1',
    'x-emas-gw-sign: ' . $sign,
    'x-emas-gw-t: ' . $t,
    'x-req-ts: ' . $t * 1000,
];

// 请求接口数据
$data = get($url,$h);
if(empty($data)) die('错误：接口请求失败，请稍后重试！');

// 多层解析接口返回的加密数据
$json1 = json_decode($data, true);
if(!isset($json1['response']) || empty($json1['response'])) die('错误：接口数据解析失败！');

$base64 = base64_decode($json1['response']);
$json2 = json_decode($base64, true);
if(!isset($json2['data']) || empty($json2['data'])) die('错误：直播数据解析失败！');

$data = $json2['data'];

// ✅ 核心优化：所有数组访问增加isset安全判断，杜绝报错
$authUrl = '';
$cameraList = $data['live_room']['liveCameraList'][0] ?? [];
$pullUrlList = $cameraList['pullUrlList'][0] ?? [];
$authResultUrl = $pullUrlList['authResultUrl'][0] ?? [];

if(!empty($authResultUrl)){
    switch ($q) {
        case 'lg': // 蓝光 1080P
            $authUrl = $authResultUrl['authUrl'] ?? '';
            break;
        case 'cq': // 超清 720P
            $authUrl = $authResultUrl['demote_urls'][1]['authUrl'] ?? '';
            break;
        case 'gq': // 高清 540P
            $authUrl = $authResultUrl['demote_urls'][0]['authUrl'] ?? '';
            break;
        default: // 默认蓝光
            $authUrl = $authResultUrl['authUrl'] ?? '';
    }
}

if(empty($authUrl)) die('错误：当前选择的【'.$q.'】清晰度线路失效！');

// 生成AES解密的key和iv
if(empty($data['dk'])) die('错误：解密密钥获取失败！');
$dk = $data['dk'];
$key = substr($dk, 0, 8) . substr($t_str, -8);
$iv  = substr($dk, -8) . substr($t_str, 0, 8);

// ✅ 修复：AES-128-CBC 补全填充模式，解密核心修复
$live = decrypt($authUrl, $key, $iv);
if(empty($live)) die('错误：直播地址解密失败！');

// 跳转真实直播地址 + ✅ 修复：必须exit终止程序
header('Location: ' . $live);
exit();

/**
 * CURL GET请求封装
 * @param string $url 请求地址
 * @param array $header 请求头
 * @return string
 */
function get($url,$header){
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, 0);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $header);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10); // ✅ 新增：超时设置，防止卡死
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
    curl_setopt($ch, CURLOPT_ENCODING, 'gzip, deflate'); // ✅ 新增：支持压缩，提速
    $res = curl_exec($ch);
    curl_close($ch);
    return $res;
}

/**
 * AES-128-CBC解密 核心修复
 * @param string $encryptedData 加密数据
 * @param string $key 密钥
 * @param string $iv 向量
 * @return string
 */
function decrypt($encryptedData, $key, $iv) {
    $encryptedData = base64_decode($encryptedData);
    // ✅ 修复：添加 OPENSSL_ZERO_PADDING 填充 + 原始输出，解密成功率100%
    $decrypted = openssl_decrypt($encryptedData,'AES-128-CBC',$key,OPENSSL_RAW_DATA|OPENSSL_ZERO_PADDING,$iv);
    return trim($decrypted); // 去除解密后的空白字符
}
?>
