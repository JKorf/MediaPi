(function () {

    angular.module('pi-test').factory('HistoryFactory', function ($q, $http) {
        var factory = {};
        var watched = [];

        factory.AddWatchedShow = function(showId, title, img, epiSeason, epiNr, watchedAt){
            factory.GetWatched().then(function(){
                $http.post("/database/add_watched_episode?showId=" + showId
                        + "&title=" + encodeURIComponent(title)
                        + "&image=" + encodeURIComponent(img)
                        + "&episodeSeason=" + epiSeason
                        + "&episodeNumber=" + epiNr
                         + "&watchedAt=" + encodeURIComponent(watchedAt)).then(function(){
                              retrieve();
                         });
            });
        }

        factory.AddWatchedMovie = function(movieId, title, img, watchedAt){
            factory.GetWatched().then(function(){
                $http.post("/database/add_watched_movie?movieId=" + movieId
                        + "&title=" + encodeURIComponent(title)
                        + "&image=" + encodeURIComponent(img)
                         + "&watchedAt=" + encodeURIComponent(watchedAt)).then(function(){
                              retrieve();
                         });
            });
        }

        factory.AddWatchedFile = function(title, url, watchedAt){
            factory.GetWatched().then(function(){
                $http.post("/database/add_watched_file?"
                        + "title=" + encodeURIComponent(title)
                        + "&url=" + encodeURIComponent(url)
                         + "&watchedAt=" + encodeURIComponent(watchedAt)).then(function(){
                              retrieve();
                         });

            });
        }

        factory.AddWatchedYouTube = function(title, watchedAt){
            factory.GetWatched().then(function(){
                $http.post("/database/add_watched_youtube?"
                        + "title=" + encodeURIComponent(title)
                         + "&watchedAt=" + encodeURIComponent(watchedAt)).then(function(){
                              retrieve();
                         });

            });
        }

        factory.RemoveWatched = function(id){
            $http.post("/database/remove_watched?"
                        + "id=" + id).then(function(){
                              retrieve();
                         });
        };

        factory.GetWatched = function(){
            var promise = $q.defer();

            if(watched.length == 0)
                retrieve().then(function(){
                    promise.resolve(watched);
                });
            else
                promise.resolve(watched);

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
            $http.get("/database/get_history").then(function(data){

                watched = [];
                for(var i = 0; i < data.data.length; i++)
                    watched.push(parse_history(data.data[i]));

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
                "WatchedAt": new Date(obj[5]),
                "Season": obj[6],
                "Episode": obj[7],
                "URL": obj[8],
                "MediaFile": obj[9]
            }
        }

        return factory;
    });

})();