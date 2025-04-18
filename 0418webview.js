function main(item) {
    let url = item.url;
    let id = ku9.getQuery(url, "id"); // 從URL中獲取id參數
    
    // 統一使用桌面端User-Agent
    let headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
    };

    // 將注入到網頁中的JavaScript代碼
    const jscode = `(function(){
        const startTime = Date.now();
        
        // 設置頁面基本樣式
        document.documentElement.style.backgroundColor = 'black';
        document.documentElement.style.height = '10%';
        document.documentElement.style.margin = '0';
        document.documentElement.style.padding = '0';
        
        document.body.style.visibility = 'hidden';
        document.body.style.margin = '0';
        document.body.style.padding = '0';
        document.body.style.minHeight = '10vh';
        
        // 在Shadow DOM中尋找video元素
        function getVideoParentShadowRoots() {
            const allElements = document.querySelectorAll('*');
            for(const element of allElements) {
                const shadowRoot = element.shadowRoot;
                if(shadowRoot) {
                    const video = shadowRoot.querySelector('video');
                    if(video) return video;
                }
            }
            return null;
        }
        
        // 移除視頻控制條
        function removeControls() {
            ['#control_bar', '.controls', '.vjs-control-bar', 'xg-controls'].forEach(selector => {
                document.querySelectorAll(selector).forEach(e => e.remove());
            });
        }
        
        // 設置視頻播放器
        function setupVideo(video) {
            const container = document.createElement('div');
            container.style.position = 'fixed';
            container.style.top = '0';
            container.style.left = '0';
            container.style.width = '100vw';
            container.style.height = '100vh';
            container.style.zIndex = '2147483647';
            container.style.backgroundColor = 'black';
            
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'fill';
            video.style.transform = 'translateZ(0)';
            
            container.appendChild(video);
            document.body.appendChild(container);
            
            document.body.style.overflow = 'hidden';
            document.documentElement.style.overflow = 'hidden';
            
            // 進入全屏模式
            const enterFullscreen = () => {
                if(container.requestFullscreen) {
                    container.requestFullscreen();
                } else if(container.webkitRequestFullscreen) {
                    container.webkitRequestFullscreen();
                }
                
                const fullscreenStyle = () => {
                    video.style.objectFit = 'contain';
                    container.style.width = '100%';
                    container.style.height = '100%';
                };
                
                container.addEventListener('fullscreenchange', fullscreenStyle);
                
                video.muted = false;
                video.volume = 1;
                video.playsInline = false;
                video.setAttribute('playsinline', 'false');
                
                try {
                    video.play();
                } catch(e) {
                    video.muted = true;
                    video.play();
                }
            };
            
            setTimeout(enterFullscreen, 300);
        }
        
        // 檢查視頻元素
        function checkVideo() {
            if(Date.now() - startTime > 15000) { // 15秒超時
                clearInterval(interval);
                document.body.style.visibility = 'visible';
                document.documentElement.style.visibility = 'visible';
                return;
            }
            
            let video = document.querySelector('video') || getVideoParentShadowRoots();
            
            if(video && video.readyState > 0) {
                clearInterval(interval);
                removeControls();
                setupVideo(video);
                
                if(video.requestFullscreen) {
                    video.requestFullscreen();
                } else if(video.webkitRequestFullscreen) {
                    video.webkitRequestFullscreen();
                }
                
                document.body.style.visibility = 'visible';
                document.documentElement.style.visibility = 'visible';
            }
        }
        
        const interval = setInterval(checkVideo, 100);
    })();`;
    
    return {
        webview: id,       // 網頁視圖使用的URL路徑
        headers: headers,  // 請求頭信息
        jscode: jscode     // 要注入的JavaScript代碼
    };
}
