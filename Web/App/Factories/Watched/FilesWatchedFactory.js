(function () {

    angular.module('pi-test').factory('FilesWatchedFactory', function ($q, $http) {
        var factory = {};
        var watchedFiles;

        factory.AddWatchedFile = function(url, watchedAt){
            factory.GetWatchedFiles().then(function(){
                watchedFiles.push({url: url, watchedAt: watchedAt});
                $http.post("/database/add_watched_file?url=" + encodeURIComponent(url) + "&watchedAt=" + encodeURIComponent(watchedAt));
            });
        }

        factory.GetWatchedFiles = function(){
            var promise = $q.defer();
            if(!watchedFiles){
                $http.get("/database/get_watched_files").then(function(data){
                    watchedFiles = [];
                    for(var i = 0; i < data.data.length; i++){
                        watchedFiles.push({
                            url: data.data[i][0],
                            watchedAt: new Date(data.data[i][1])
                        });
                    }
                    console.log(watchedFiles);
                    promise.resolve(watchedFiles);
                });
            }else
            {
                promise.resolve(watchedFiles);
            }

            return promise.promise;
        }

        return factory;
    });

})();