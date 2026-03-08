<?php
header('Content-Type: application/x-mpegurl');
header('Content-Disposition: attachment; filename="playlist.m3u"');

/**
 * 獲取央視頻頻道資料並轉換為 M3U 播放列表
 */
function generatePlaylist() {
    $apiUrl = 'https://capi.yangshipin.cn/api/oms/pc/page/PG00000004.json';
    
    // 獲取 API 內容
    $response = file_get_contents($apiUrl);
    if (!$response) {
        die("#EXTM3U\n# Error fetching API data");
    }

    $data = json_decode($response, true);
    $channelList = $data['data']['feedModuleList'][0]['dataTvChannelList'] ?? [];

    echo "#EXTM3U x-tvg-url=\"http://51zmt.top\"\n";

    foreach ($channelList as $channel) {
        $name = $channel['channelName'];
        $logo = $channel['tvLogo'];
        $streamId = $channel['streamId'];
        $pid = $channel['pid'];
        
        // 組合播放地址
        $playUrl = "http://43.156.8.127:5050/ysp?id={$streamId}&pid={$pid}&q=fhd";

        // 輸出 M3U 格式內容
        echo "#EXTINF:-1 tvg-name=\"{$name}\" tvg-logo=\"{$logo}\" group-title=\"央視投屏\",{$name}\n";
        echo "{$playUrl}\n";
    }
}

generatePlaylist();
