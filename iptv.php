<?php
// PHP Version: 8.0+

// 配置文件和环境变量
$config = [
    'name' => 'Sync IPTV Playlists',
    'permissions' => [
        'contents' => 'write',
    ],
    'base_url' => 'https://mursor.ottiptv.cc',
    'files' => [
        'iptv.m3u',
        'yylunbo.m3u',
        'huyayqk.m3u',
        'douyuyqk.m3u',
        'bililive.m3u',
    ],
    // 环境变量，从外部获取
    'token' => getenv('M3U_TOKEN'),
];

/**
 * 带有重试机制的下载函数
 *
 * @param string $url 下载链接
 * @param string $outfile 目标文件名
 * @param int $maxAttempts 最大重试次数
 * @return bool 是否下载成功
 */
function downloadWithRetry($url, $outfile, $maxAttempts = 5) {
    $tmpfile = "$outfile.tmp";

    if (file_exists($tmpfile)) {
        unlink($tmpfile);
    }

    for ($attempt = 1; $attempt <= $maxAttempts; $attempt++) {
        echo "➡️  [$attempt/$maxAttempts] 下载 $outfile ...\n";

        // 使用 wget 命令进行下载，并捕获输出和状态
        // -q: 静默模式
        // -O: 输出到指定文件
        $command = "wget -q --timeout=15 --connect-timeout=10 \"$url\" -O \"$tmpfile\"";
        exec($command, $output, $status);

        if ($status === 0 && filesize($tmpfile) > 0) {
            // 下载成功且文件不为空
            rename($tmpfile, $outfile);
            echo "✅ $outfile 下载并覆盖完成\n";
            return true;
        }

        echo "⚠️  $outfile 下载失败，等待 $attempt 秒后重试...\n";
        sleep($attempt);
    }

    echo "❌ $outfile 最终下载失败，保留旧版本\n";
    if (file_exists($tmpfile)) {
        unlink($tmpfile);
    }
    return false;
}

// 主程序入口
function main() {
    global $config;

    echo "🎵 开始下载 IPTV 播放列表...\n";

    // 假设 Git 仓库已检出
    // 可以通过 PHP 的 `exec` 或 `shell_exec` 执行 Git 命令
    // exec('git checkout .', $output, $status); // 确保工作目录干净

    // 下载所有文件
    $allFilesDownloaded = true;
    foreach ($config['files'] as $file) {
        $url = "{$config['base_url']}/{$file}?token={$config['token']}";
        // 即使下载失败，也继续处理下一个文件
        if (!downloadWithRetry($url, $file)) {
            $allFilesDownloaded = false;
        }
    }

    // 检查文件下载状态
    echo "\n📊 文件下载状态：\n";
    $filesChanged = false;
    foreach ($config['files'] as $file) {
        if (file_exists($file) && filesize($file) > 0) {
            echo "✅ $file - " . filesize($file) . " 字节\n";
            $filesChanged = true; // 简化判断，只要有文件下载成功就认为有变更
        } else {
            echo "❌ $file - 文件不存在或为空\n";
        }
    }
    
    if (!$filesChanged) {
        echo "\nℹ️ 没有检测到任何文件被成功下载，跳过提交。\n";
        return;
    }

    // Git 操作
    // 配置用户信息
    exec('git config --local user.name "github-actions[bot]"');
    exec('git config --local user.email "github-actions[bot]@users.noreply.github.com"');

    // 添加并提交文件
    $filesToAdd = implode(' ', $config['files']);
    exec("git add $filesToAdd", $output, $status);
    if ($status === 0) {
        $commitMessage = "chore: auto-update IPTV playlists - " . date('Y-m-d H:i:s T');
        exec("git commit -m \"$commitMessage\"", $output, $status);
        if ($status === 0) {
            echo "✅ 文件已提交\n";
        } else {
            echo "❌ Git commit 失败\n";
        }
    } else {
        echo "❌ Git add 失败\n";
    }

    // 推送更改
    // 假设你有一个 `push.php` 或在主脚本中调用此逻辑
    exec("git push origin " . 'master', $output, $status); // 这里需要获取分支名，以'master'为例
    if ($status === 0) {
        echo "🚀 更新已推送到仓库\n";
    } else {
        echo "❌ Git push 失败\n";
    }
}

// 执行主函数
main();
