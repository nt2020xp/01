<?php
/*
# -*- coding: utf-8 -*-
# 快直播.php
# @Author  : Doubebly
# @Time    : 2025/6/7 21:11
*/

$keys = ['578', '579', '580', '581', '582', '583', '584', '585', '586', '587', '588', '589', '590', '591', '592', '593', '594', '595', '596', '597', '598', '599', '600', '601', '602', '603', '604', '605', '606', '607', '608', '609', '610', '611', '612', '613', '614', '615', '616', '617', '618', '619', '620', '621', '622', '623', '624'];
$values = [];

$url = "https://jzb5kqln.huajiaedu.com/prod-api/iptv/getIptvList";
$curl = curl_init();
curl_setopt_array($curl, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_ENCODING => '',
    CURLOPT_MAXREDIRS => 10,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
    CURLOPT_SSL_VERIFYPEER => 0,
    CURLOPT_SSL_VERIFYHOST => 0,
    CURLOPT_CUSTOMREQUEST => 'GET',
    CURLOPT_HTTPHEADER => [
        'User-Agent: Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Mobile Safari/537.36 EdgA/136.0.0.0',
    ],
]);
$response = curl_exec($curl);
$err = curl_error($curl);
curl_close($curl);
$data_list = json_decode($response, true)['list'];
foreach ($data_list as $k) {
    $values[strval($k['id'])] = $k;
}
$tv_list = ['#EXTM3U'];
foreach ($keys as $v) {
    $c = $values[$v];
    $name = $c['play_source_name'];
    $group_name = strstr($name, 'CCTV') ? "央视频道" : "卫视频道" ;
    $tv_list[] = "#EXTINF:-1 tvg-id=\"\" tvg-name=\"\" tvg-logo=\"https://logo.doube.eu.org/{$name}.png\" group-title=\"{$group_name}\",{$name}";
    $tv_list[] = $c['play_source_url'];
}
header("Content-type: text/plain; charset=utf-8");
echo join("\n", $tv_list);
exit();
