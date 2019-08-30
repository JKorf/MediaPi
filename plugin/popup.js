var allSrcs = [];
var totalFrames = 0;
var framesReturned = 0;
var changed = false;

function add_sources (results){
	framesReturned += 1;
	results = results + "";
	var srcs = results.split(",");
	
	for(var i =0 ; i < srcs.length; i++){
		if(srcs[i].length === 0)
			continue;
		allSrcs.push(srcs[i]);
	}
	changed = true;
}

function show_videos(){
	
	if(!changed)
		return;
	
	var html = "";
	if(allSrcs.length === 0 && framesReturned === totalFrames){
		html = "<div class='title'>No videos found</div>";
	}
	else
	{	
		var html = "<div class='title'>Videos found on page:</div>";
		changed = false;
		for (var i = 0; i < allSrcs.length; i++){			
			html += "<div class='video-result'><div class='video-url'><input type='text' value='" + allSrcs[i] + "' readonly enabled='false'/></div><div class='url-copy'><img src='/copy.png' /></div></div>";
		}
	}		
	
	html += "<div class='frames-info'>scanned " + framesReturned + "/" + totalFrames + " frame(s)</div>";
	
	document.querySelector("#videos").innerHTML = html;
	$(".url-copy").click(function(e){
		var input = $(e.target).closest(".video-result").find("input")[0];
		input.select();
		input.setSelectionRange(0, 99999);
		document.execCommand('copy');
	});
}

chrome.tabs.query({active: true}, function(tabs) {
	var tab = tabs[0];	
	chrome.webNavigation.getAllFrames({tabId:tab.id},function(frames){		
		totalFrames = frames.length;
		for(var i = 0; i < frames.length; i++){
		  chrome.tabs.executeScript(tab.id, {
			frameId: frames[i].frameId,
			file: "/scripts.js",
			matchAboutBlank: true
		  }, add_sources);
		}
	});  
});

show_videos();
setInterval(show_videos, 100);