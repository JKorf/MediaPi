

chrome.runtime.onMessage.addListener( function(request, sender, sendResponse) {
    if(location.href.startsWith("https://www.youtube.com")){
		var split = location.href.split("&");
		sendResponse({data: [split[0]], success: true});
		return;
	}
	
	
	var videos =  $("video");
	var data = [];
	for(var i = 0; i< videos.length; i++){
		var src = GetSource($(videos[i]));
		data.push(src);
	}
    sendResponse({data: data, success: true});
});

function GetSource(video){
	var src = video.attr("src");
	
	if(src == null){
		var childSources = video.children("source");
		if(childSources.length)
			src = childSources.eq(0).attr("src");
	}

	if(src == null)
		return;

	var loc = location.href.substring(0, location.href.lastIndexOf('/')) + "/";
	
	src = src.replace("blob:", "");

	if(!src.startsWith("http"))
		loc += src;
	else
		loc = src;
	return loc;
}



(function(){
	return;
setTimeout(function() {
	return;
	var videos = $("video");
	for(var i = 0; i < videos.length; i++){
		var vid = $(videos[i]);
		vid.click(function(ev){
			console.log(ev);
			var src = GetSource(vid);
			var w = window.open("http://localhost/movies/play_from_extension?url=" + encodeURIComponent(src) + "&title=Test");
			setTimeout(function(){
				w.close();
			}, 500);
			
			return false;
		});
	}
}, 1000);


})();