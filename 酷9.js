function main(item) {
    let url = item.url;
    let id = ku9.getQuery(url, "id");
    let domain = id.split('/');
    let headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    };
    
const jscode=`(function(){
    const startTime = Date.now();
    let Video = null;
    let hi = null;
    let isDraggingProgress = false;

    // 控制栏移除
    function removeControls() {
        const selectors = ['#control_bar','.controls','.vjs-control-bar','xg-controls','.xgplayer-ads','.fixed-layer','div[style*="z-index: 9999"]'];
        selectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(e => e.remove());
        });
        
    }
    
    // 视频比例切换
    window.setscale = function(scaletype) {
        if (!Video) return;
        const container = Video.parentElement;
        Video.style.position = 'absolute';
        Video.style.top = '50%';
        Video.style.left = '50%';
        Video.style.transform = 'translate(-50%, -50%)';
        Video.style.outline = "none";
        Video.style.border = "none";
        Video.style.boxShadow = "none";
        switch (scaletype) {
            case 0: // 默认(原比例最大化)
                Video.style.width = '100%';
                Video.style.height = '100%';
                Video.style.objectFit  = 'contain';
                break;
            case 1: // 16:9
                Video.style.width = 'auto';
                Video.style.height = '100%';
                Video.style.objectFit = 'fill';
                Video.style.aspectRatio = '16/9';
                break;
            case 2: // 4:3
                Video.style.width = 'auto';
                Video.style.height = '100%';
                Video.style.objectFit = 'fill';
                Video.style.aspectRatio = '4/3';
                break;
            case 3: // 填充
                Video.style.width = '100%';
                Video.style.height = '100%';
                Video.style.objectFit = 'fill';
                break;
            case 4: // 原始
                Video.style.width = 'auto';
                Video.style.height = hi;
                Video.style.objectFit = 'contain';
                break;
            case 5: // 裁剪
                Video.style.width = '100%';
                Video.style.height = '100%';
                Video.style.objectFit = 'cover';
                Video.style.aspectRatio = 'none';
                break;
        }
    }

    // 视频状态同步
    function syncVideoState() {
        if (!Video) return;
        
        // 同步总时长
        ku9.setduration(Video.duration);
        
        // 持续同步播放进度
        function updateProgress() {
            if (!isDraggingProgress) {
                ku9.setposition(Video.currentTime);
            }
            requestAnimationFrame(updateProgress);
        }
        updateProgress();
    }

    // 键盘事件监听
    function handleKeyPress(e) {
        if (!Video) return;
        
        // 防抖处理（300ms内不重复响应）
        clearTimeout(keyDebounceTimer);
        keyDebounceTimer = setTimeout(() => {
            switch(e.keyCode) {
                // 播放/暂停控制
                case 32:   // 空格键
                case 13:   // 回车键（PC）
                case 179:  // 媒体播放暂停键（部分遥控器）
                case 415:  // 媒体播放键（Android TV）
                    Video.paused ? Video.play() : Video.pause();
                    break;
                
                // 快退控制
                case 37:    // 左箭头（PC）
                case 21:    // 左方向键（Android TV）
                case 812:   // 遥控器左键（部分机顶盒）
                    Video.currentTime = Math.max(0, Video.currentTime - 10);
                    break;
                
                // 快进控制
                case 39:    // 右箭头（PC）
                case 22:    // 右方向键（Android TV）
                case 813:   // 遥控器右键（部分机顶盒）
                    Video.currentTime = Math.min(Video.duration, Video.currentTime + 10);
                    break;
            }
            
            // 阻止默认行为
            e.preventDefault();
            e.stopPropagation();
        }, 100);
    }
    
    // 视频容器设置
    function setupVideo(video) {
        Video = video;
        const container = document.createElement('div');
        container.id = 'video-fullscreen-container';
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100vw';
        container.style.height = '100vh';
        container.style.zIndex = '2147483647';
        container.style.backgroundColor = 'black';
        container.style.overflow = 'hidden';
        container.style.transform = 'translateZ(0)';

        setscale(ku9.getscale());
        document.body.appendChild(container);
        container.appendChild(video);

        const enterFullscreen = () => {
            const fullscreenElem = container.requestFullscreen ? container : video;
            const requestFS = fullscreenElem.requestFullscreen || 
                            fullscreenElem.webkitRequestFullscreen || 
                            fullscreenElem.mozRequestFullScreen;

            if(requestFS) {
                requestFS.call(fullscreenElem).catch(() => {
                    container.style.width = window.innerWidth+'px';
                    container.style.height = window.innerHeight+'px';
                });
            }
            video.muted = false;
            video.volume = 1;
        };
        setTimeout(enterFullscreen, 100);
        
        // 事件监听
        Video.addEventListener('play', () => ku9.play());
        Video.addEventListener('pause', () => ku9.pause());
        Video.addEventListener('timeupdate', () => ku9.setposition(Video.currentTime));
        
        // 初始化状态同步
        syncVideoState();
        
        // 添加键盘监听
        document.addEventListener('keydown', handleKeyPress);
    }

    // 实现控制函数
    window.pause = function() {
        Video && Video.pause();
    }
    
    window.play = function() {
        Video && Video.play();
    }
    
    window.setposition = function(position) {
        if (Video) {
            isDraggingProgress = true;
            Video.currentTime = position;
            // 延迟更新防止拖动卡顿
            setTimeout(() => isDraggingProgress = false, 100);
        }
    }

    // 事件监听
    function handleVideoElement(video) {
        if (video.tagName !== 'VIDEO' || Video) return;
        if (video.paused) video.play();
        const onReady = () => {
            removeControls();
            if (video.paused) video.play();
            const width = video.videoWidth || 0;
            const height = video.videoHeight || 0;
            hi = height/1080*100 + '%';
            setupVideo(video);
            ku9.setvideo(width, height);
            ku9.setaudio("立体声");
        };

        if (video.readyState >= 1) {
            onReady();
        } else {
            video.addEventListener('canplay', onReady, {once: true});
        }
    }
    
       // 监听视频元素
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeName === 'VIDEO') {
                    handleVideoElement(node);
                } else if (node.querySelectorAll) {
                    node.querySelectorAll('video').forEach(handleVideoElement);
                }
            });
        });
    });

    document.querySelectorAll('video').forEach(handleVideoElement);
    observer.observe(document.documentElement, {
        childList: true,
        subtree: true
    });

    setTimeout(() => observer.disconnect(), 15000);

    // 移动端适配
    const viewportMeta = document.createElement('meta');
    viewportMeta.name = "viewport";
    viewportMeta.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no";
    document.head.appendChild(viewportMeta);
    
    
})();`;

    return {
        webview: id,
        headers :headers,
        jscode: jscode
    };
}
