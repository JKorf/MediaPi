(function () {

    angular.module('pi-test').factory('FilesWatchedFactory', function (MemoryFactory) {
        var factory = {};
        var watchedFiles;

        factory.AddWatchedFile = function(url, watchedAt){
            if (!watchedFiles)
                watchedFiles = factory.GetWatchedFiles();

            var maxlen = 300
            if(watchedFiles.length == maxlen){
                watchedFiles.sort(function(a, b) {
                    a = new Date(a.watchedAt);
                    b = new Date(b.watchedAt);
                    return a<b ? -1 : a>b ? 1 : 0;
                });
                watchedFiles.splice(0,1)
            }

            var updated = false;
            for(var i = 0; i < watchedFiles.length; i++){
                if(watchedFiles[i].url == url){
                    watchedFiles[i].watchedAt = watchedAt;
                    updated = true;
                    break;
                }
            }

            if(!updated)
                watchedFiles.push({url: url, watchedAt: watchedAt});
            MemoryFactory.SetValue("WatchedFiles", watchedFiles);
        }

        factory.GetWatchedFiles = function(){
           if (!watchedFiles){
                watchedFiles = MemoryFactory.GetValue("WatchedFiles");
                if(!watchedFiles)
                    watchedFiles = [];
            }

            return watchedFiles;
        }

        return factory;
    });

})();