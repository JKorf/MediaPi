
var vidSources = "";
function getVideosInDoc(doc){	
	var vids = doc.getElementsByTagName('video');
	for(var i = 0; i < vids.length; i++)
		vidSources += vids[i].currentSrc + ",";
}

getVideosInDoc(document);

vidSources