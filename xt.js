
function main(item) {
  const url = item.url;  // 从输入的 `item` 对象中提取 `url`
  const field = { url };  // 初始化一个包含 `url` 的对象 `field`

  // `fieldMaps` 是一个包含不同网站域名的映射表，根据不同的域名匹配不同的视频提取规则
  const fieldMaps = {
    '.4gtv.tv': { contains: 'cdn.hinet.net/live/' },  // 4gtv.tv 域名匹配，包含特定字符串 'cdn.hinet.net/live/'
    'mjv003.com': { verify: 'Eighteen_declaration_2023.png' },  // mjv003.com 域名匹配，验证图片 'Eighteen_declaration_2023.png'
    'yeslivetv.com': {
      container: '#iframe,.video-container,iframe',  // 指定视频容器的选择器
      contains: '.m3u8,.googlevideo.com/videoplayback',  // 包含的媒体格式或 URL
      filter: 'static-mozai.4gtv.tv'  // 过滤掉的 URL
    },
    'www.ofiii.com': { container: '.player_fixed_section' },  // ofiii.com 域名匹配，指定视频容器的选择器
    'www.gdtv.cn': { index: 2 },  // gdtv.cn 域名匹配，指定索引为 2 的某个元素
    'www.chaojidianshi.net': { filter: 'www.google.com' },  // chaojidianshi.net 域名匹配，过滤掉 'www.google.com' 的 URL
    'huya.com': { contains: '.flv' },  // huya.com 域名匹配，包含 .flv 格式的视频
    'douyin.com': { contains: '.flv' },  // douyin.com 域名匹配，包含 .flv 格式的视频
    'iptv345.com': { contains: 'iptv200.com/play.php?token=' },  // iptv345.com 域名匹配，包含特定的 URL
    'cntv.cn': { container: '.video-container, video', contains: '.m3u8,.mp4' },  // miguvideo.com 匹配，提取视频容器和支持的格式
    'cctv.com': { container: '.video-container, video', contains: '.m3u8,.mp4' }  // miguvideo.com 匹配，提取视频容器和支持的格式
    'www.kds.tw': { container: '.video-container, video', contains: '.m3u8,.mp4' },  // www.kds.tw 匹配，提取视频容器和支持的格式
  };

  // 遍历 `fieldMaps` 对象中的每个域名规则
  for (const [key, value] of Object.entries(fieldMaps)) {
    if (url.includes(key)) {  // 如果当前 `url` 包含某个域名
      Object.assign(field, value);  // 将匹配的规则合并到 `field` 对象中
      break;  // 找到匹配项后终止循环
    }
  }

  return jz.getVideo(field);  // 调用 `jz.getVideo` 函数并传入 `field` 对象，获取视频信息
}
