<?php
//脚本生成时间：2026-01-21 09:48:09
header('Content-Type: text/plain; charset=utf-8');
error_reporting(0);
function get_curl($url,$download=false){
    $ch=curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_SSL_VERIFYPEER,false);
    curl_setopt($ch,CURLOPT_SSL_VERIFYHOST,false);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);          
    curl_setopt($ch, CURLOPT_CONNECTTIMEOUT,10); 
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1); 
    curl_setopt($ch, CURLOPT_MAXREDIRS, 5);
    if($download){
        curl_setopt($ch, CURLOPT_BUFFERSIZE, 128000);
        curl_setopt($ch, CURLOPT_WRITEFUNCTION, 'stream');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, false);
    }else{
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    }
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
   
}
function creat_m3u8($id,$qlt,$alt,$proxy){
    $timestamp = intval(time()/4-355017628);
    $t=$timestamp*4;
    $m3u8 = "#EXTM3U\n";
    $m3u8.= "#EXT-X-VERSION:3\n";
    $m3u8.= "#EXT-X-TARGETDURATION:4\n";
    $m3u8.= "#EXT-X-MEDIA-SEQUENCE:{$timestamp}\n";
    for ($i=0; $i<10; $i++) {
        $m3u8.= "#EXTINF:4,\n";
        if($proxy!="true"){
            $m3u8.="https://ntd-tgc.cdn.hinet.net/live/pool/{$id}/litv-pc/{$id}-avc1_6000000={$qlt}-mp4a_134000_zho={$alt}-begin={$t}0000000-dur=40000000-seq={$timestamp}.ts\n";
        }else{
            $m3u8.=get_path()."?id={$id}&url=".urlencode("https://ntd-tgc.cdn.hinet.net/live/pool/{$id}/litv-pc/{$id}-avc1_6000000={$qlt}-mp4a_134000_zho={$alt}-begin={$t}0000000-dur=40000000-seq={$timestamp}.ts")."\n";
        }
        $timestamp = $timestamp+1;
        $t=$t+4;
    }
    return $m3u8;
}
function get_path() {
    $protocol = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? "https" : "http";
    return $protocol . "://" . $_SERVER['HTTP_HOST'] . $_SERVER['SCRIPT_NAME'];
}
function stream($ch, $data) {
    if (connection_aborted()) {
        return 0;
    }
    echo $data;
    ob_flush();
    flush();
    return strlen($data);
}
function creat_m3u($n,$proxy){
    $m3u="#EXTM3U x-tvg-url=".'"https://epg.iill.top/epg.xml.gz"'."\n";
    $local_path = get_path();
    if($proxy=="true"){
        $proxy="&proxy=true";
    }else{
         $proxy="";
    }
    foreach ($n as $id => $key ){
        $m3u.='#EXTINF:-1 tvg-id="'.$id.'" tvg-name="'.$key[4].'" tvg-logo="https://epg.iill.top/logo/'.$key[2].'.png" group-title="'.$key[3].'",'.$key[4]."\n{$local_path}?id={$id}{$proxy}\n";
    }
    return $m3u;
}
$n = [
//以下参数为脚本每4小时自动生成一次
"4gtv-4gtv002"=>[1,11,"民視","綜合頻道","民視"],
"4gtv-4gtv003"=>[1,7,"民視第一台","綜合頻道","民視第一台"],
"litv-ftv13"=>[1,7,"民視新聞台","新聞財經","民視新聞台"],
"4gtv-4gtv001"=>[1,7,"民視台灣台","綜合頻道","民視台灣台"],
"litv-ftv09"=>[1,6,"民視影劇台","電影戲劇","民視影劇台"],
"litv-ftv07"=>[1,6,"民視旅遊台","科教紀實","民視旅遊台"],
"4gtv-4gtv004"=>[1,9,"民視綜藝台","綜藝娛樂","民視綜藝台"],
"4gtv-4gtv040"=>[1,7,"中视","綜合頻道","中視"],
"4gtv-4gtv074"=>[1,6,"中视新闻","新聞財經","中視新聞台"],
"4gtv-4gtv009"=>[2,9,"中天新闻","新聞財經","中天新聞台"],
"4gtv-4gtv041"=>[1,7,"華視","綜合頻道","華視"],
"4gtv-4gtv052"=>[1,6,"華視新聞","新聞財經","華視新聞"],
"4gtv-4gtv046"=>[1,7,"靖天綜合台","綜合頻道","靖天綜合台"],
"4gtv-4gtv063"=>[1,8,"靖天國際台","綜合頻道","靖天國際台"],
"4gtv-4gtv058"=>[1,9,"靖天戲劇台","電影戲劇","靖天戲劇台"],
"4gtv-4gtv047"=>[1,2,"靖天日本台","綜合頻道","靖天日本台"],
"4gtv-4gtv055"=>[1,9,"靖天映畫台","電影戲劇","靖天映畫台"],
"4gtv-4gtv044"=>[1,7,"靖天卡通台","卡通動漫","靖天卡通台"],
"4gtv-4gtv062"=>[1,9,"靖天育樂台","綜藝娛樂","靖天育樂台"],
"4gtv-4gtv065"=>[1,9,"靖天資訊台","新聞財經","靖天資訊台"],
"4gtv-4gtv061"=>[1,7,"靖天電影台","電影戲劇","靖天電影台"],
"4gtv-4gtv054"=>[1,9,"靖天歡樂台","綜藝娛樂","靖天歡樂台"],
"litv-xinchuang12"=>[10003,20000,"龍華偶像台","電影戲劇","龍華偶像台"],
"litv-xinchuang01"=>[10002,20000,"龍華卡通台","卡通動漫","龍華卡通台"],
"litv-xinchuang18"=>[10003,20000,"龍華戲劇台","電影戲劇","龍華戲劇台"],
"litv-xinchuang11"=>[10003,20000,"龍華日韓台","電影戲劇","龍華日韓台"],
"litv-xinchuang21"=>[10003,20000,"龍華經典台","電影戲劇","龍華經典台"],
"litv-xinchuang03"=>[10003,20000,"龍華電影台","電影戲劇","龍華電影台"],
"litv-xinchuang02"=>[10003,20000,"龍華洋片台","電影戲劇","龍華洋片台"],
"4gtv-4gtv045"=>[1,7,"靖洋戲劇台","電影戲劇","靖洋戲劇台"],
"4gtv-4gtv057"=>[1,7,"靖洋卡通-Nice-Bingo","卡通動漫","靖洋卡通NiceBingo"],
"litv-longturn14"=>[1,6,"寰宇新聞台","新聞財經","寰宇新聞台"],
"4gtv-4gtv156"=>[1,8,"寰宇新聞台灣台","新聞財經","寰宇新聞台灣台"],
"4gtv-4gtv158"=>[1,2,"寰宇財經台","新聞財經","寰宇財經台"],
"4gtv-4gtv067"=>[1,9,"TVBS精采","綜藝娛樂","TVBS精采台"],
"4gtv-4gtv034"=>[1,7,"八大精彩台","綜藝娛樂","八大精彩台"],
"4gtv-4gtv039"=>[1,6,"八大綜藝台","綜藝娛樂","八大綜藝台"],
"4gtv-4gtv070"=>[1,9,"ELTA娛樂","綜藝娛樂","ELTA娛樂台"],
"litv-xinchuang20"=>[10003,20000,"ELTA生活英語","科教紀實","ELTV生活英語"],
"4gtv-4gtv152"=>[1,7,"东森新闻","新聞財經","東森新聞"],
"4gtv-4gtv153"=>[1,6,"东森财经","新聞財經","東森財經新聞"],
"4gtv-4gtv075"=>[1,6,"鏡電視新聞台","新聞財經","鏡電視新聞台"],
"4gtv-4gtv076"=>[1,7,"亞洲旅遊台","科教紀實","亞洲旅遊台"],
"4gtv-4gtv053"=>[1,9,"GINX-Esports-TV","體育競技","GINXEsportsTV"],
"4gtv-4gtv014"=>[1,6,"时尚运动X","體育競技","時尚運動X"],
"4gtv-4gtv101"=>[1,6,"智林体育","體育競技","智林體育台"],
"4gtv-4gtv077"=>[1,5,"TraceSports","體育競技","TraceSports"],
"4gtv-4gtv011"=>[1,7,"影迷數位電影台","電影戲劇","影迷數位電影台"],
"4gtv-4gtv017"=>[1,7,"AMC-最愛電影","電影戲劇","AMC電影台"],
"4gtv-4gtv042"=>[1,7,"公視戲劇台","電影戲劇","公視戲劇台"],
"4gtv-4gtv049"=>[1,9,"采昌影劇台","電影戲劇","采昌影劇台"],
"litv-xinchuang22"=>[10003,20000,"台灣戲劇台","電影戲劇","台灣戲劇台"],
"litv-ftv15"=>[1,7,"影迷數位紀實台","科教紀實","影迷數位紀實台"],
"4gtv-4gtv018"=>[1,7,"達文西頻道","科教紀實","達文西頻道"],
"4gtv-4gtv059"=>[1,7,"Classica-古典樂","科教紀實","Classica古典樂"],
"4gtv-4gtv083"=>[1,6,"Mezzo-Live","科教紀實","MezzoLive"],
"4gtv-4gtv006"=>[1,10,"豬哥亮歌廳秀","綜藝娛樂","豬哥亮歌廳秀"],
"4gtv-4gtv082"=>[1,7,"Trace-Urban","體育競技","TraceUrban"],
"4gtv-4gtv016"=>[1,7,"韩国娱乐台KMTV","綜藝娛樂","韓國娛樂台"],
"4gtv-4gtv079"=>[1,8,"Arirang-TV","新聞財經","ArirangTV"],
"litv-ftv10"=>[1,7,"MCE","電影戲劇","MCE 我的歐洲電影"],
"4gtv-4gtv104"=>[1,7,"第1商业台","新聞財經","第1商業台"],
"4gtv-4gtv110"=>[1,6,"Pet-Club-TV","科教紀實","Pet Club TV"],
"litv-xinchuang19"=>[10003,20000,"Smart-知識台","科教紀實","Smart知識台"],
"4gtv-4gtv013"=>[1,7,"視納華仁紀實頻道","科教紀實","視納華仁紀實頻道"],
"4gtv-4gtv043"=>[1,7,"客家電視台","綜合頻道","客家電視台"],
"litv-ftv16"=>[1,6,"好消息","綜合頻道","好消息"],
"litv-ftv17"=>[1,6,"好消息2台","綜合頻道","好消息2台"],
"4gtv-4gtv084"=>[1,7,"國會頻道1","科教紀實","國會頻道1"],
"4gtv-4gtv085"=>[1,6,"國會頻道2","科教紀實","國會頻道2"],

//如遇到音视频参数变动，需手动修改以下数字部分
"4gtv-4gtv155"=>[1,7,"民視","綜合頻道","民視"],
"4gtv-4gtv080"=>[1,8,"中视经典","綜藝娛樂","中視經典台"],
"4gtv-4gtv064"=>[1,9,"中視菁采台","綜藝娛樂","中視菁采台"],
"4gtv-4gtv109"=>[1,9,"中天亚洲","綜合頻道","中天亞洲台"],
"4gtv-4gtv073"=>[1,6,"TVBS","綜合頻道","TVBS"],
"4gtv-4gtv072"=>[1,6,"TVBS新闻","新聞財經","TVBS新聞台"],
"4gtv-4gtv068"=>[1,8,"TVBS欢乐","綜藝娛樂","TVBS歡樂台"],
"4gtv-4gtv066"=>[1,6,"台視","綜合頻道","台視"],
"4gtv-4gtv051"=>[1,6,"台視新聞台","新聞財經","台視新聞台"],
"4gtv-4gtv056"=>[1,6,"台視財經台","新聞財經","台視財經台"],
"litv-xinchuang07"=>[10003,20000,"博斯运动1","體育競技","博斯運動一台"],
"litv-xinchuang08"=>[10003,20000,"博斯运动1","體育競技","博斯運動二台"],
"litv-xinchuang10"=>[10003,20000,"博斯无限","體育競技","博斯無限台"],
"litv-xinchuang13"=>[10003,20000,"博斯无限2","體育競技","博斯無限二台"],
"litv-xinchuang09"=>[10003,20000,"博斯网球","體育競技","博斯網球台"],
"litv-xinchuang05"=>[10003,20000,"博斯高球1","體育競技","博斯高球台"],
"litv-xinchuang06"=>[10003,20000,"博斯高球2","體育競技","博斯高球二台"],
"litv-xinchuang04"=>[10003,20000,"博斯魅力","體育競技","博斯魅力台"],
"4gtv-4gtv010"=>[1,7,"非凡新聞台","新聞財經","非凡新聞台"],
"4gtv-4gtv048"=>[1,7,"非凡商業台","新聞財經","非凡商業台"],
"litv-ftv03"=>[1,7,"VOA-美國之音","新聞財經","VOA美國之音"],
];
$id = $_GET['id'] ?? '';
$url= $_GET['url'] ?? '';
$proxy = $_GET['proxy'] ?? '';
if(empty(trim($id))){
    die(creat_m3u($n,$proxy)); 
}
if(!isset($n[$id])){
    header("HTTP/1.1 404 Not Found");
    die('Channel not found');
}
if(empty(trim($url))){
    $m3u8 = creat_m3u8($id, $n[$id][0], $n[$id][1],$proxy);
    header('Content-Type: application/vnd.apple.mpegurl');
    header('Content-Disposition: inline; filename=index.m3u8');
    die(trim($m3u8));
}
header('X-Accel-Buffering: no');
header('Content-Disposition: inline; filename=stream.ts');
get_curl($url,true);
exit;
