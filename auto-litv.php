<?php
//脚本生成时间：2026-01-09 04:02:59
header('Content-Type: text/plain; charset=utf-8');
error_reporting(0);
function creat_m3u8($id,$qlt,$alt){
    $timestamp = intval(time()/4-355017628);
    $t=$timestamp*4;
    $m3u8 = "#EXTM3U\n";
    $m3u8.= "#EXT-X-VERSION:3\n";
    $m3u8.= "#EXT-X-TARGETDURATION:4\n";
    $m3u8.= "#EXT-X-MEDIA-SEQUENCE:{$timestamp}\n";
    for ($i=0; $i<10; $i++) {
        $m3u8.= "#EXTINF:4,\n";
        $m3u8.="https://ntd-tgc.cdn.hinet.net/live/pool/{$id}/litv-pc/{$id}-avc1_6000000={$qlt}-mp4a_134000_zho={$alt}-begin={$t}0000000-dur=40000000-seq={$timestamp}.ts\n";
        $timestamp = $timestamp+1;
        $t=$t+4;
    }
    return $m3u8;
}
function get_path() {
    $protocol = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? "https" : "http";
    return $protocol . "://" . $_SERVER['HTTP_HOST'] . $_SERVER['SCRIPT_NAME'];
}
function creat_m3u($n){
    $m3u="#EXTM3U\n";
    $local_path = get_path();
    foreach ($n as $id => $key ){
        $m3u.='#EXTINF:-1 tvg-id="'.$id.'" tvg-name="'.$key[2].'" group-title="LITV系列",'.$key[2]."\n{$local_path}?id={$id}\n";
    }
    return $m3u;
}
$n = [
//以下参数为脚本每4小时自动生成一次
"4gtv-4gtv003"=>[1,7,"民視第一台"],
"litv-ftv13"=>[1,7,"民視新聞台"],
"4gtv-4gtv001"=>[1,7,"民視台灣台"],
"litv-ftv09"=>[1,6,"民視影劇台"],
"litv-ftv07"=>[1,6,"民視旅遊台"],
"4gtv-4gtv004"=>[1,9,"民視綜藝台"],
"4gtv-4gtv040"=>[1,7,"中視"],
"4gtv-4gtv074"=>[1,6,"中視新聞台"],
"4gtv-4gtv009"=>[2,9,"中天新聞台"],
"4gtv-4gtv041"=>[1,7,"華視"],
"4gtv-4gtv052"=>[1,6,"華視新聞"],
"4gtv-4gtv063"=>[1,8,"靖天國際台"],
"4gtv-4gtv058"=>[1,9,"靖天戲劇台"],
"4gtv-4gtv047"=>[1,2,"靖天日本台"],
"4gtv-4gtv044"=>[1,7,"靖天卡通台"],
"4gtv-4gtv062"=>[1,9,"靖天育樂台"],
"4gtv-4gtv065"=>[1,9,"靖天資訊台"],
"4gtv-4gtv061"=>[1,7,"靖天電影台"],
"4gtv-4gtv054"=>[1,9,"靖天歡樂台"],
"litv-longturn12"=>[5,2,"龍華偶像台"],
"litv-longturn01"=>[4,5,"龍華卡通台"],
"litv-longturn18"=>[5,6,"龍華戲劇台"],
"litv-longturn11"=>[5,2,"龍華日韓台"],
"litv-longturn21"=>[5,6,"龍華經典台"],
"litv-longturn03"=>[5,6,"龍華電影台"],
"litv-longturn02"=>[5,2,"龍華洋片台"],
"4gtv-4gtv045"=>[1,7,"靖洋戲劇台"],
"4gtv-4gtv057"=>[1,7,"靖洋卡通NiceBingo"],
"litv-longturn14"=>[1,6,"寰宇新聞台"],
"4gtv-4gtv156"=>[1,8,"寰宇新聞台灣台"],
"4gtv-4gtv158"=>[1,2,"寰宇財經台"],
"4gtv-4gtv073"=>[1,6,"TVBS"],
"4gtv-4gtv068"=>[1,8,"TVBS歡樂台"],
"4gtv-4gtv067"=>[1,9,"TVBS精采台"],
"4gtv-4gtv034"=>[1,7,"八大精彩台"],
"4gtv-4gtv039"=>[1,6,"八大綜藝台"],
"4gtv-4gtv070"=>[1,9,"ELTA娛樂台"],
"litv-longturn20"=>[5,7,"ELTV生活英語"],
"4gtv-4gtv152"=>[1,7,"東森新聞"],
"4gtv-4gtv153"=>[1,6,"東森財經新聞"],
"4gtv-4gtv075"=>[1,6,"鏡電視新聞台"],
"4gtv-4gtv076"=>[1,7,"亞洲旅遊台"],
"4gtv-4gtv053"=>[1,9,"GINXEsportsTV"],
"4gtv-4gtv014"=>[1,6,"時尚運動X"],
"4gtv-4gtv101"=>[1,6,"智林體育台"],
"4gtv-4gtv077"=>[1,5,"TraceSports"],
"4gtv-4gtv011"=>[1,7,"影迷數位電影台"],
"4gtv-4gtv017"=>[1,7,"AMC電影台"],
"4gtv-4gtv042"=>[1,7,"公視戲劇台"],
"4gtv-4gtv049"=>[1,9,"采昌影劇台"],
"litv-longturn22"=>[5,2,"台灣戲劇台"],
"litv-ftv15"=>[1,7,"影迷數位紀實台"],
"4gtv-4gtv018"=>[1,7,"達文西頻道"],
"4gtv-4gtv059"=>[1,7,"Classica古典樂"],
"4gtv-4gtv083"=>[1,6,"MezzoLive"],
"4gtv-4gtv006"=>[1,10,"豬哥亮歌廳秀"],
"4gtv-4gtv082"=>[1,7,"TraceUrban"],
"4gtv-4gtv016"=>[1,7,"韓國娛樂台"],
"litv-ftv10"=>[1,7,"MCE 我的歐洲電影"],
"4gtv-4gtv104"=>[1,7,"第1商業台"],
"4gtv-4gtv110"=>[1,6,"Pet Club TV"],
"litv-longturn19"=>[5,7,"Smart知識台"],
"4gtv-4gtv013"=>[1,7,"視納華仁紀實頻道"],
"4gtv-4gtv043"=>[1,7,"客家電視台"],
"litv-ftv16"=>[1,6,"好消息"],
"litv-ftv17"=>[1,6,"好消息2台"],
"4gtv-4gtv084"=>[1,7,"國會頻道1"],
"4gtv-4gtv085"=>[1,6,"國會頻道2"],

//如遇到音视频参数变动，需手动修改以下数字部分
"4gtv-4gtv002"=>[1,11,"民視"],
"4gtv-4gtv155"=>[1,7,"民視"],
"4gtv-4gtv080"=>[1,8,"中視經典台"],
"4gtv-4gtv064"=>[1,9,"中視菁采台"],
"4gtv-4gtv109"=>[1,9,"中天亞洲台"],
"4gtv-4gtv046"=>[1,7,"靖天綜合台"],
"4gtv-4gtv055"=>[1,9,"靖天映畫台"],
"4gtv-4gtv072"=>[1,6,"TVBS新聞台"],
"4gtv-4gtv066"=>[1,6,"台視"],
"4gtv-4gtv051"=>[1,6,"台視新聞台"],
"4gtv-4gtv056"=>[1,6,"台視財經台"],
"litv-longturn07"=>[5,2,"博斯運動一台"],
"litv-longturn08"=>[5,2,"博斯運動二台"],
"litv-longturn10"=>[5,2,"博斯無限台"],
"litv-longturn13"=>[4,6,"博斯無限二台"],
"litv-longturn09"=>[5,2,"博斯網球台"],
"litv-longturn05"=>[5,2,"博斯高球台"],
"litv-longturn06"=>[5,2,"博斯高球二台"],
"litv-longturn04"=>[5,7,"博斯魅力台"],
"4gtv-4gtv010"=>[1,7,"非凡新聞台"],
"4gtv-4gtv048"=>[1,7,"非凡商業台"],
"4gtv-4gtv079"=>[1,8,"ArirangTV"],
"litv-ftv03"=>[1,7,"VOA美國之音"],
];
$id = $_GET['id'] ?? '';
if(empty(trim($id))){
    die(creat_m3u($n)); 
}
if(!isset($n[$id])){
    header("HTTP/1.1 404 Not Found");
    die('Channel not found');
}
$m3u8 = creat_m3u8($id, $n[$id][0], $n[$id][1]);
header('Content-Type: application/vnd.apple.mpegurl'); 
header('Content-Disposition: inline; filename=index.m3u8');
die(trim($m3u8));
