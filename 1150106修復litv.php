
<?php
/*
 * LiTV 直播源生成器（优化完整版）
 * 版本：v1.2
 * 原作者：leifeng
 * 优化：GPT-5
 * 最后修改：2025-11-12
 * 功能说明：
 *   - http://yourserver/litv.php?token=xxxx        → 返回完整 M3U 列表
 *   - http://yourserver/litv.php?token=xxxx&id=频道ID → 返回指定频道的 M3U8 播放列表
 */

header('Content-Type: text/plain; charset=utf-8');

// ========== 基本配置 ==========
$SECRET_TOKEN = 'cnbkk'; // 修改为你自己的 token
$DEFAULT_GROUP = 'LITV';

// ========== Token 验证 ==========
$token = $_GET['token'] ?? '';
if ($token !== $SECRET_TOKEN) {
    http_response_code(403);
    exit("Error: Access denied. Invalid or missing token.\n");
}

// ========== 频道映射表 ==========
$channels = [
	//新闻频道
	'4gtv-4gtv009' => [2, 9, '中天新闻', '中天新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中天新闻.png',''],
	'4gtv-4gtv072' => [1, 6, 'TVBS新闻', 'TVBS新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/TVBS新闻.png',''],
	'4gtv-4gtv152' => [1, 7, '东森新闻', '东森新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/东森新闻.png',''],
	'litv-ftv13' => [1, 9, '民视新闻', '民视新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视新闻.png',''],
	'4gtv-4gtv075' => [1, 6, '镜电视新闻', '镜新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/镜电视新闻.png',''],
	'4gtv-4gtv010' => [1, 7, '非凡新闻', '非凡新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/非凡新闻.png',''],
	'4gtv-4gtv051' => [1, 6, '台视新闻', '台视新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/台视新闻.png',''],
	'4gtv-4gtv052' => [1, 6, '华视新闻', '华视新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/华视新闻.png',''],
	'4gtv-4gtv074' => [1, 6, '中视新闻', '中视新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中视新闻.png',''],
	'litv-longturn14' => [1, 7, '寰宇新闻', '寰宇新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/寰宇新闻.png',''],
	'4gtv-4gtv156' => [1, 8, '寰宇新闻台湾', '寰宇新闻台湾', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/寰宇新闻台湾.png',''],
	'litv-ftv10' => [1, 7, '半岛国际新闻', '半岛新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/半岛国际新闻.png',''],
	'litv-ftv03' => [1, 9, '美国之音', '美国之音', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/美国之音.png',''],

	//财经频道
	'4gtv-4gtv153' => [1, 9, '东森财经新闻', '东森财经新闻', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/东森财经新闻.png',''],
	'4gtv-4gtv048' => [1, 6, '非凡商业', '非凡商业', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/非凡商业.png',''],
	'4gtv-4gtv056' => [1, 6, '台视财经', '台视财经', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/台视财经.png',''],
	'4gtv-4gtv104' => [1, 7, '第1商业台', '第1商业台', 'https://p-cdnstatic.svc.litv.tv/pics/logo_litv_4gtv-4gtv104_pc.png',''],

	//综合频道
	'4gtv-4gtv073' => [1, 6, 'TVBS', 'TVBS', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/TVBS.png',''],
	'4gtv-4gtv066' => [1, 7, '台视', '台视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/台视.png',''],
	'4gtv-4gtv040' => [1, 7, '中视', '中视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中视.png',''],
	'4gtv-4gtv041' => [1, 7, '华视', '华视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/华视.png',''],
	'4gtv-4gtv002' => [1, 11, '民视', '民视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视.png',''],
	'4gtv-4gtv155' => [1, 7, '民视', '民视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视.png',''],
	'4gtv-4gtv001' => [1, 7, '民视台湾', '民视台湾', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视台湾.png',''],
	'4gtv-4gtv003' => [1, 7, '民视第一', '民视第一', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视第一.png',''],
	'4gtv-4gtv109' => [1, 9, '中天亚洲', '中天亚洲', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中天亚洲.png',''],
	'4gtv-4gtv046' => [1, 7, '靖天综合', '靖天综合', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天综合.png',''],
	'4gtv-4gtv063' => [1, 8, '靖天国际', '靖天国际', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天国际.png',''],
	'4gtv-4gtv065' => [1, 9, '靖天资讯', '靖天资讯', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天资讯.png',''],
	'4gtv-4gtv043' => [1, 7, '客家电视', '客家电视', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/客家电视.png',''],
	'4gtv-4gtv079' => [1, 8, 'ARIRANG', '阿里郎', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/ARIRANG.png',''],
	'4gtv-4gtv084' => [1, 9, '国会频道1', '国会频道1', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/国会频道1.png',''],
	'4gtv-4gtv085' => [1, 6, '国会频道2', '国会频道2', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/国会频道2.png',''],

	//娱乐综艺频道
	'4gtv-4gtv068' => [1, 8, 'TVBS欢乐', 'TVBS欢乐', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/TVBS欢乐.png',''],
	'4gtv-4gtv067' => [1, 9, 'TVBS精采', 'TVBS精采', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/TVBS精采.png',''],
	'4gtv-4gtv070' => [1, 9, 'ELTV娱乐', '爱尔达娱乐', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/爱尔达娱乐.png',''],
	'4gtv-4gtv004' => [1, 9, '民视综艺', '民视综艺', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视综艺.png',''],
	'4gtv-4gtv039' => [1, 8, '八大综艺', '八大综艺', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/八大综艺.png',''],
	'4gtv-4gtv034' => [1, 7, '八大精彩', '八大精彩', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/八大精彩.png',''],
	'4gtv-4gtv054' => [1, 9, '靖天欢乐', '靖天欢乐', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天欢乐.png',''],
	'4gtv-4gtv062' => [1, 9, '靖天育乐', '靖天育乐', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天育乐.png',''],
	'4gtv-4gtv064' => [1, 9, '中视菁采', '中视菁采', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中视菁采.png',''],
	'4gtv-4gtv006' => [1, 10, '猪哥亮歌厅秀', '猪哥亮歌厅秀', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/猪哥亮歌厅秀.png',''],

	//电影频道
	'4gtv-4gtv011' => [1, 7, '影迷數位電影', '影迷數位電影', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/影迷数位电影.png',''],
	'4gtv-4gtv017' => [1, 7, 'amc电影', 'amc电影', 'https://4gtvimg2.4gtv.tv/4gtv-Image/Channel/mobile/logo_4gtv_4gtv-4gtv017new_mobile.png',''],
	'4gtv-4gtv061' => [1, 7, '靖天电影', '靖天电影', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天电影.png',''],
	'4gtv-4gtv055' => [1, 9, '靖天映画', '靖天映画', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天映画.png',''],
	'4gtv-4gtv049' => [1, 9, '采昌影剧', '采昌影剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/采昌影剧.png',''],
	'litv-ftv09' => [1, 6, '民视影剧', '民视影剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视影剧.png',''],
	'litv-longturn03' => [5, 6, '龙华电影', '龙华电影', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华电影.png',''],
	'litv-longturn02' => [5, 2, '龙华洋片', '龙华洋片', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华洋片.png',''],

	//戏剧频道
	'4gtv-4gtv042' => [1, 7, '公视戏剧', '公视戏剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/公视戏剧.png',''],
	'4gtv-4gtv045' => [1, 7, '靖洋戏剧', '靖洋戏剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖洋戏剧.png',''],
	'4gtv-4gtv058' => [1, 9, '靖天戏剧', '靖天戏剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天戏剧.png',''],
	'4gtv-4gtv080' => [1, 8, '中视经典', '中视经典', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/中视经典.png',''],
	'4gtv-4gtv047' => [1, 2, '靖天日本', '靖天日本', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天日本.png',''],
	'litv-longturn18' => [5, 6, '龙华戏剧', '龙华戏剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华戏剧.png',''],
	'litv-longturn11' => [5, 2, '龙华日韩', '龙华日韩', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华日韩.png',''],
	'litv-longturn12' => [5, 2, '龙华偶像', '龙华偶像', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华偶像.png',''],
	'litv-longturn21' => [5, 6, '龙华经典', '龙华经典', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华经典.png',''],
	'litv-longturn22' => [5, 2, '台湾戏剧', '台湾戏剧', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/台湾戏剧.png',''],

	//体育频道
	'4gtv-4gtv014' => [1, 6, '时尚运动X', '时尚运动X', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/时尚运动X.png',''],
	'4gtv-4gtv053' => [1, 9, 'GINXEsportsTV', 'GinxTV', 'https://p-cdnstatic.svc.litv.tv/pics/logo_litv_4gtv-4gtv053_pc.png',''],
	'4gtv-4gtv101' => [1, 6, '智林体育', '智林体育', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/智林体育.png',''],
	'litv-longturn04' => [5, 7, '博斯魅力', '博斯魅力', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯魅力.png',''],
	'litv-longturn05' => [5, 2, '博斯高球1', '博斯高球1', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯高球1.png',''],
	'litv-longturn06' => [5, 2, '博斯高球2', '博斯高球2', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯高球2.png',''],
	'litv-longturn07' => [5, 2, '博斯运动1', '博斯运动1', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯运动1.png',''],
	'litv-longturn08' => [5, 2, '博斯运动2', '博斯运动2', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯运动2.png',''],
	'litv-longturn09' => [5, 2, '博斯网球1', '博斯网球', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯网球.png',''],
	'litv-longturn10' => [5, 2, '博斯无限1', '博斯无限', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯无限.png',''],
	'litv-longturn13' => [4, 6, '博斯无限2', '博斯无限2', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/博斯无限2.png',''],

	//纪实/知识/旅游频道
	'4gtv-4gtv013' => [1, 7, '视纳华仁纪实', '视纳华仁纪实', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/视纳华仁纪实.png',''],
	'4gtv-4gtv016' => [1, 7, 'Globetrotter', 'Globetrotter', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/GLOBALTREKKER.png',''],
	'4gtv-4gtv018' => [1, 7, '达文西频道', '达文西频道', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/达文西.png',''],
	'4gtv-4gtv076' => [1, 7, '亚洲旅游', '亚洲旅游', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/亚洲旅游.png',''],
	'litv-ftv07' => [1, 9, '民视旅游', '民视旅游', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/民视旅游.png',''],
	'litv-longturn19' => [5, 9, 'Smart知识台', 'Smart知识台', 'https://p-cdnstatic.svc.litv.tv/pics/logo_litv_litv-longturn19_pc.png',''],

	//儿童/卡通频道
	'4gtv-4gtv044' => [1, 9, '靖天卡通', '靖天卡通', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖天卡通.png',''],
	'4gtv-4gtv057' => [1, 7, '靖洋卡通', '靖洋卡通', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/靖洋卡通.png',''],
	'litv-longturn01' => [4, 6, '龙华卡通', '龙华卡通', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/龙华卡通.png',''],

	//音乐/艺术频道
	'4gtv-4gtv059' => [1, 7, 'CLASSICA古典乐', '古典音乐', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/CLASSICA古典乐.png',''],
	'4gtv-4gtv082' => [1, 7, 'TraceUrban', 'TRACE URBAN', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/TRACEURBAN.png',''],
	'4gtv-4gtv083' => [1, 8, 'MezzoLiveHD', 'MEZZO LIVE', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/MEZZOLIVEHD.png',''],

	//教育/宗教频道
	'litv-ftv16' => [1, 6, '好消息1', '好消息1', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/好消息1.png',''],
	'litv-ftv17' => [1, 6, '好消息2', '好消息2', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/好消息2.png',''],
	'litv-longturn20' => [5, 7, 'ELTV生活英语', '生活英语', 'https://gcore.jsdelivr.net/gh/taksssss/tv/icon/ELTV生活英语.png','']
];

$id = isset($_GET['id']) ? $_GET['id'] : null;


// ========== 获取 base URL ==========
function getBaseUrl() {
    if (php_sapi_name() === 'cli') return 'http://localhost';
    $https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ||
             (isset($_SERVER['SERVER_PORT']) && $_SERVER['SERVER_PORT'] == 443);
    $protocol = $https ? 'https' : 'http';
    $host = $_SERVER['HTTP_X_FORWARDED_HOST'] ??
            $_SERVER['HTTP_HOST'] ??
            ($_SERVER['SERVER_NAME'] ?? 'localhost');
    return $protocol . '://' . $host;
}
$base_url = getBaseUrl();

// ========== 参数 ==========
$id = $_GET['id'] ?? null;

// ========== 无 id：返回完整 M3U ==========
if (!$id) {
    echo "#EXTM3U\n";
    foreach ($channels as $key => $v) {
        $group = $v[5] ?: $GLOBALS['DEFAULT_GROUP'];
        $tvgId = $v[2];
        $name  = $v[3];
        $logo  = $v[4];
        $url   = "{$base_url}/litv.php?token=" . urlencode($GLOBALS['SECRET_TOKEN']) . "&id=" . urlencode($key);
        echo "#EXTINF:-1 tvg-id=\"{$tvgId}\" tvg-name=\"{$name}\" tvg-logo=\"{$logo}\" group-title=\"{$group}\",{$name}\n";
        echo "{$url}\n";
    }
    exit;
}

// ========== 有 id：返回单频道 M3U8 ==========
if (!isset($channels[$id])) {
    http_response_code(404);
    exit("Error: Channel not found.\n");
}

$timestamp = intval(time() / 4 - 355017625);
$t = $timestamp * 4;

$m3u8 = "#EXTM3U\n";
$m3u8 .= "#EXT-X-VERSION:3\n";
$m3u8 .= "#EXT-X-TARGETDURATION:4\n";
$m3u8 .= "#EXT-X-MEDIA-SEQUENCE:{$timestamp}\n";

for ($i = 0; $i < 3; $i++) {
    $m3u8 .= "#EXTINF:4,\n";
    $m3u8 .= sprintf(
        "https://ntd-tgc.cdn.hinet.net/live/pool/%s/litv-pc/%s-avc1_6000000=%d-mp4a_134000_zho=%d-begin=%d0000000-dur=40000000-seq=%d.ts\n",
        $id, $id, $channels[$id][0], $channels[$id][1], $t, $timestamp
    );
    $timestamp++;
    $t += 4;
}

header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename="' . $id . '.m3u8"');
header('Content-Length: ' . strlen($m3u8));
echo $m3u8;
?>

