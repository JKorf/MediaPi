
var vidSources = "";
function getVideosInDoc(doc){	
	if(doc.URL.startsWith("https://www.youtube.com/embed/")){		
		vidSources += "https://www.youtube.com/watch?v=" + doc.URL.substring(30, doc.URL.indexOf('?'));
		return vidSources;
	}
	
	if(doc.URL.startsWith("https://www.youtube.com/watch?"))
	{
		vidSources += doc.URL;
		return vidSources;
	}
	
	var vids = doc.getElementsByTagName('video');
	for(var i = 0; i < vids.length; i++)
		vidSources += vids[i].currentSrc + ",";
}

getVideosInDoc(document);

vidSources