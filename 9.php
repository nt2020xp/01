<?php
/*
使用方法 litv.php?id=4gtv-4gtv001
无参数时返回完整频道列表，格式：频道名称,https://ip/litv.php?id=频道ID
https://1234.koyeb.app/litv.php
*/
header('Content-Type: text/plain; charset=utf-8');

$channels = [    
    '4gtv-4gtv072' => ['TVBS新聞台', 1, 2],
    '4gtv-4gtv152' => ['東森新聞台', 1, 6],
    'litv-ftv13' => ['民視新聞台', 1, 7],
    '4gtv-4gtv052' => ['華視新聞', 1, 2],
    '4gtv-4gtv074' => ['中視新聞', 1, 2],
    '4gtv-4gtv051' => ['台視新聞', 1, 2],
    '4gtv-4gtv009' => ['中天新聞台', 2, 7],
    '4gtv-4gtv153' => ['東森財經台', 1, 2],
    'litv-longturn14' => ['寰宇新聞台', 4, 2],
    '4gtv-4gtv156' => ['寰宇台灣台', 1, 6],
    '4gtv-4gtv158' => ['寰宇財經台', 5, 2],    
    '4gtv-4gtv075' => ['鏡新聞', 1, 2],
    '4gtv-4gtv010' => ['非凡新聞台', 1, 6],
    '4gtv-4gtv048' => ['非凡商業台', 1, 2],
    '4gtv-4gtv047' => ['靖天日本台', 1, 8],
    'litv-ftv07' => ['民視旅遊台', 1, 7],
    '4gtv-4gtv076' => ['亞洲旅遊台', 1, 2],
    'litv-longturn19' => ['Smart知識台', 5, 6],
    '4gtv-4gtv041' => ['華視', 1, 8],
    '4gtv-4gtv040' => ['中視', 1, 8],
    '4gtv-4gtv066' => ['台視', 1, 2],
    '4gtv-4gtv155' => ['民視', 1, 6],  
    '4gtv-4gtv062' => ['靖天育樂台', 1, 8],
    '4gtv-4gtv055' => ['靖天映畫台', 1, 8],  
    '4gtv-4gtv063' => ['靖天國際台', 1, 6],
    '4gtv-4gtv065' => ['靖天資訊台', 1, 8],
    '4gtv-4gtv061' => ['靖天電影台', 1, 7],
    '4gtv-4gtv046' => ['靖天綜合台', 1, 8],
    '4gtv-4gtv058' => ['靖天戲劇台', 1, 8],
    '4gtv-4gtv054' => ['靖天歡樂台', 1, 8],
    '4gtv-4gtv045' => ['靖洋戲劇台', 1, 8],   
    '4gtv-4gtv044' => ['靖天卡通台', 1, 8],
    '4gtv-4gtv057' => ['靖洋卡通台', 1, 8],   
    'litv-longturn02' => ['龍華洋片台', 5, 2],
    'litv-longturn03' => ['龍華電影台', 5, 6],
    'litv-longturn11' => ['龍華日韓台', 5, 2],
    'litv-longturn12' => ['龍華偶像台', 5, 2],
    'litv-longturn18' => ['龍華戲劇台', 5, 6],
    'litv-longturn21' => ['龍華經典台', 5, 2],
    'litv-longturn01' => ['龍華卡通台', 1, 2],
    '4gtv-4gtv011' => ['影迷數位電影台', 1, 6],
    '4gtv-4gtv001' => ['民視台灣台', 1, 6],
    '4gtv-4gtv003' => ['民視第一台', 1, 6],
    '4gtv-4gtv004' => ['民視綜藝台', 1, 8],
    'litv-ftv09' => ['民視影劇台', 1, 2],
    '4gtv-4gtv064' => ['中視菁采台', 1, 8],   
    '4gtv-4gtv080' => ['中視經典台', 1, 6],
    '4gtv-4gtv067' => ['TVBS精采台', 1, 8],
    '4gtv-4gtv068' => ['TVBS歡樂台', 1, 7],
    '4gtv-4gtv034' => ['八大精彩台', 1, 6],
    '4gtv-4gtv039' => ['八大綜藝台', 1, 7],   
    '4gtv-4gtv070' => ['愛爾達娛樂台', 1, 7], 
    '4gtv-4gtv049' => ['采昌影劇台', 1, 8],   
    '4gtv-4gtv006' => ['豬哥亮歌廳秀', 1, 9],   
    '4gtv-4gtv013' => ['視納華仁紀實頻道', 1, 6],
    '4gtv-4gtv014' => ['時尚運動X', 1, 5],
    '4gtv-4gtv018' => ['達文西頻道', 1, 8],   
    '4gtv-4gtv042' => ['公視戲劇', 1, 6],
    '4gtv-4gtv043' => ['客家電視台', 1, 9],           
    '4gtv-4gtv053' => ['GINX Esports TV', 1, 8],    
    '4gtv-4gtv056' => ['台視財經', 1, 2],  
    '4gtv-4gtv059' => ['CLASSICA 古典樂', 1, 6],     
    '4gtv-4gtv073' => ['TVBS', 1, 2],  
    '4gtv-4gtv077' => ['TRACE Sport Stars', 1, 7],
    '4gtv-4gtv079' => ['ARIRANG阿里郎頻道', 1, 2],   
    '4gtv-4gtv082' => ['TRACE Urban', 1, 6],
    '4gtv-4gtv083' => ['Mezzo Live HD', 1, 6],
    '4gtv-4gtv084' => ['國會頻道1台', 1, 6],
    '4gtv-4gtv085' => ['國會頻道2台', 1, 5],
    '4gtv-4gtv101' => ['智林體育台', 1, 5],
    '4gtv-4gtv102' => ['東森購物1台', 1, 6],
    '4gtv-4gtv103' => ['東森購物2台', 1, 6],
    '4gtv-4gtv104' => ['第1商業台', 1, 7],
    '4gtv-4gtv109' => ['中天亞洲台', 1, 6],    
    'litv-ftv03' => ['VOA美國之音', 1, 7],   
    'litv-ftv10' => ['半島國際新聞台', 1, 7],    
    'litv-ftv15' => ['影迷數位紀實台', 1, 7],
    'litv-ftv16' => ['好消息', 1, 2],
    'litv-ftv17' => ['好消息2台', 1, 2],   
    'litv-longturn04' => ['博斯魅力台', 5, 6],
    'litv-longturn05' => ['博斯高球台', 5, 2],
    'litv-longturn06' => ['博斯高球二台', 5, 2],
    'litv-longturn07' => ['博斯運動一台', 5, 2],
    'litv-longturn08' => ['博斯運動二台', 5, 2],
    'litv-longturn09' => ['博斯網球台', 5, 2],
    'litv-longturn10' => ['博斯無限台', 5, 2],    
    'litv-longturn13' => ['博斯無限二台', 4, 2],  
    'litv-longturn20' => ['ELTV生活英語台', 5, 6],   
    'litv-longturn22' => ['台灣戲劇台', 5, 2]
];

// 获取当前URL的基础部分
$baseUrl = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? "https" : "http") . "://$_SERVER[HTTP_HOST]$_SERVER[SCRIPT_NAME]";

// 如果没有参数，返回频道URL列表
if (!isset($_GET['id'])) {
    foreach ($channels as $id => $data) {
        echo $data[0] . ',' . $baseUrl . '?id=' . $id . "\n";
    }
    exit;
}

// 有参数时生成m3u8播放列表
$id = $_GET['id'];
if (!isset($channels[$id])) {
    header('HTTP/1.1 404 Not Found');
    echo "频道不存在，可用频道列表：\n";
    foreach ($channels as $cid => $cdata) {
        echo $cdata[0] . ',' . $baseUrl . '?id=' . $cid . "\n";
    }
    exit;
}

// 使用原始音频参数
$audioParam = $channels[$id][2];
$videoParam = $channels[$id][1];

$timestamp = intval(time()/4-355017625);
$t = $timestamp * 4;
$current = "#EXTM3U"."\r\n";
$current .= "#EXT-X-VERSION:3"."\r\n";
$current .= "#EXT-X-TARGETDURATION:4"."\r\n";
$current .= "#EXT-X-MEDIA-SEQUENCE:{$timestamp}"."\r\n";

for ($i = 0; $i < 3; $i++) {
    $current .= "#EXTINF:4,"."\r\n";
    $current .= "https://ntd-tgc.cdn.hinet.net/live/pool/{$id}/litv-pc/{$id}-avc1_6000000={$videoParam}-mp4a_134000_zho={$audioParam}-begin={$t}0000000-dur=40000000-seq={$timestamp}.ts"."\r\n";
    $timestamp = $timestamp + 1;
    $t = $t + 4;
}

header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename='.$id.'.m3u8');
header('Content-Length: ' . strlen($current));
echo $current;
?>
