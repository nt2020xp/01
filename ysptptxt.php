<?php
/**
 * 設定標頭為純文字格式 (UTF-8)
 * 這樣瀏覽器或播放器讀取時會直接視為文字內容
 */
header('Content-Type: text/plain; charset=utf-8');

/**
 * 獲取央視頻頻道資料並轉換為 TXT 播放列表
 */
function generateTxtPlaylist() {
    $apiUrl = 'https://yangshipin.cn';
    
    // 設定超時防止卡死
    $opts = [
        "http" => [
            "method" => "GET",
            "header" => "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n",
            "timeout" => 10
        ]
    ];
    $context = stream_context_create($opts);
    
    // 獲取 API 內容
    $response = @file_get_contents($apiUrl, false, $context);
    
    if (!$response) {
        die("錯誤：無法獲取 API 資料");
    }

    $data = json_decode($response, true);
    
    // 根據 API 結構定位頻道清單
    $channelList = $data['data']['feedModuleList'][0]['dataTvChannelList'] ?? [];

    if (empty($channelList)) {
        die("錯誤：找不到頻道清單");
    }

    // 輸出分類標題（許多 TXT 播放器支援此格式）
    echo "央視頻,#genre#\n";

    foreach ($channelList as $channel) {
        $name = $channel['channelName'];
        $streamId = $channel['streamId'];
        $pid = $channel['pid'];
        
        // 組合播放地址
        $playUrl = "http://43.156.8{$streamId}&pid={$pid}&q=fhd";

        // 輸出 TXT 格式：頻道名稱,播放地址
        echo "{$name},{$playUrl}\n";
    }
}

// 執行函數
generateTxtPlaylist();
