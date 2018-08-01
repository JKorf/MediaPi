(function () {

    angular.module('pi-test').factory('EpisodesWatchedFactory', function ($q, $http) {
        var factory = {};
        var watched;

        factory.AddWatched = function(showId, epiSeason, epiNr, watchedAt){
            factory.GetWatched().then(function(){
                var watchedShow = $.grep(watched, function(item){
                    return item.showId == showId;
                });

                $http.post("/database/add_watched_episode?showId=" + showId
                        + "&episodeSeason=" + epiSeason
                        + "&episodeNumber=" + epiNr
                         + "&watchedAt=" + encodeURIComponent(watchedAt));

                if (watchedShow.length == 0){
                    // newly show started
                    watched.push({showId: showId, episodes: [{season: epiSeason, episode: epiNr, watchedAt: watchedAt}] });
                    sort();
                }else{
                    // add episode
                    watchedShow[0].episodes.push({season: epiSeason, episode: epiNr, watchedAt: watchedAt});
                    sort();
                }
            });
        }

        factory.GetWatched = function(){
            var promise = $q.defer();
            if(!watched){
                $http.get("/database/get_watched_episodes").then(function(data){
                    watched = [];
                    for(var i = 0; i < data.data.length; i++)
                    {
                        var watchedShow = $.grep(watched, function(item){
                            return item.showId == data.data[i][0];
                        });
                        if(watchedShow.length == 0){
                           watched.push({
                           showId: data.data[i][0],
                           episodes: [
                                {season: data.data[i][1],
                                episode: data.data[i][2]}],
                                watchedAt: new Date(data.data[i][3])});
                        }
                        else{
                            watchedShow[0].episodes.push({
                                season: data.data[i][1],
                                episode: data.data[i][2],
                                watchedAt: new Date(data.data[i][3])});
                        }
                    }
                    sort();

                    console.log(watched);
                    promise.resolve(watched);
                });
            }else
            {
                promise.resolve(watched);
            }

            return promise.promise;
        }

        factory.GetWatchedForShow = function(showId){
            var promise = $q.defer();

            factory.GetWatched().then(function(){
                for(var i = 0 ; i < watched.length; i++){
                    if(watched[i].showId == showId)
                        promise.resolve(watched[i].episodes);
                }
                promise.resolve(false);
            });

            return promise.promise;
        }

        function sort(){
            watched.sort(function(a, b) {
                    a = new Date(a.watchedAt);
                    b = new Date(b.watchedAt);
                    return a>b ? -1 : a<b ? 1 : 0;
                });
        }

        return factory;
    });

})();