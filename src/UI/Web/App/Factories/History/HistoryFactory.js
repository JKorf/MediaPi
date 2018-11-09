(function () {

    angular.module('pi-test').factory('HistoryFactory', function ($q, $http, CacheFactory) {
        var factory = {};
        var watched = [];

        factory.RemoveWatched = function(id){
            $http.post("/database/remove_watched?"
                        + "id=" + id).then(function(){
                              retrieve();
                         });
        };

        factory.GetWatched = function(){
            var promise = $q.defer();

            retrieve().then(function(){
                promise.resolve(watched);
            }, function(){
                promise.reject()
            });

            return promise.promise;
        }

        factory.GetWatchedForShow = function(showId){
            var promise = $q.defer();

            factory.GetWatched().then(function(){
                var result = [];
                for(var i = 0 ; i < watched.length; i++){
                    if(watched[i].ImdbId == showId)
                        result.push(watched[i]);
                }
                promise.resolve(result);
            });

            return promise.promise;
        }

        factory.LastWatchedShow = function(){
            var promise = $q.defer();

            factory.GetWatched().then(function(){
                sort();
                promise.resolve(watched[0]);
            });

            return promise.promise;
        }

        function retrieve()
        {
            var promise = $q.defer();
            CacheFactory.Get("/database/get_history", 60).then(function(data){

                watched = [];
                for(var i = 0; i < data.length; i++)
                    watched.push(parse_history(data[i]));
                sort();
                promise.resolve(watched);
            });
            return promise.promise;
        }

        function sort(){
            watched.sort(function(a, b) {
                    a = a.WatchedAt;
                    b = b.WatchedAt;
                    return a>b ? -1 : a<b ? 1 : 0;
                });
        }

        function parse_history(obj)
        {
            return {
                "Id": obj[0],
                "ImdbId": obj[1],
                "Type": obj[2],
                "Title": obj[3],
                "Image": obj[4],
                "WatchedAt": new Date().setTime(obj[5]),
                "Season": obj[6],
                "Episode": obj[7],
                "URL": obj[8],
                "MediaFile": obj[9]
            }
        }

        return factory;
    });

})();