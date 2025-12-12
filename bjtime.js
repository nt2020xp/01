var swfCanvas = document.getElementById("swf_clock");
var swfCtrl = undefined;
function getSWFVersion(){
    var n = navigator;
    if (n.plugins && n.mimeTypes.length) {
        var a = n.plugins["Shockwave Flash"];
        if (a && a.description) {
            return a.description.replace(/([a-zA-Z]|\s)+/, "").replace(/(\s)+r/, ".") + ".0";
        }
    }
    else 
        if (window.ActiveXObject && !window.opera) {
            for (var i = 10; i >= 2; i--) {
                try {
                    var c = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.' + i);
                    if (c) {
                        return i + ".0.0";
                        break;
                    }
                } 
                catch (e) {
                }
            }
        }
}

function creatFlashfunction(id,url, width, height, fq){
    var str = "<object classid='clsid:D27CDB6E-AE6D-11cf-96B8-444553540000' width=" + width + " height=" + height + " name='"+fq+"' id='"+id+"'>";
    str += "<param name='movie' value=" + url + ">";
    str += "<param name=FlashVars value=" + fq + ">";
    str += "<param name='menu' value='false'>";
    str += "<param name='wmode' value='opaque'>";
    str += "<param name='allowfullscreen' value='false'>";
    str += "<param name='allowscriptaccess' value='always'>";
    str += "<embed id='"+id+"_ff' FlashVars='"+fq+"' src='" + url + "' quality='high' pluginspage='http://www.adobe.com/shockwave/download/download.cgi?P1_Prod_Version=ShockwaveFlash' type='application/x-shockwave-flash' width=" + width + " height=" + height + " menu='false' allowfullscreen='false' allowscriptaccess='always' name='flashResult' wmode='opaque'/>";
    str += "</object>";
   	swfCanvas.innerHTML = str;
}

function getSWF(movieName) {
	var isIE = navigator.userAgent.indexOf('MSIE') != -1 && !window.opera;
	if(isIE){
		return document[movieName] || window[movieName];
	}else {
		return document[movieName+"_ff"] || window[movieName+"_ff"];
	}
    
};


(function(){
	var swfVer=getSWFVersion();
	if(swfVer==undefined||swfVer.split(".")[0]<8){}
	else {
		swfCanvas.className = "swfBox";
		creatFlashfunction("bd_swf_clock","http://www.wofav.cn/img/clock.swf","64px","64px","");
		swfCtrl = getSWF("bd_swf_clock");
		setTimeout(function(){
			if (!swfLoaded) swfCanvas.style.display = "none";
		},5000);
	}
})();


