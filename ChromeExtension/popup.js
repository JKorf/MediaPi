document.addEventListener('DOMContentLoaded', function() {
		
	chrome.tabs.query({active: true, currentWindow: true}, function(tabs) 
	{
		chrome.tabs.sendMessage(tabs[0].id, {msg: "getVideos"}, function(response) 
		{
			for(var i = 0; i < response.data.length; i++){
				$(".container").append(
				"<div class='video' src='"+response.data[i]+"'>" +
					"<div class='title'>Video</div>" + 
					"<div class='src'>" + response.data[i] + "</div>" +
				 "</div>")
			}
			
			setTimeout(function(){
				$(".video").click(function(ev){
					var url = "http://localhost/movies/play_from_extension?url=" + encodeURIComponent($(ev.target).closest(".video").attr("src")) + "&title=Test";
					console.log(url);
					var w = window.open(url);
					setTimeout(function(){
						w.close();
					}, 500);
				});				
			});
		});
	});
	
	
});

