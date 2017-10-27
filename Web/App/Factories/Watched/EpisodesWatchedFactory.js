(function () {

    angular.module('pi-test').factory('EpisodesWatchedFactory', function (MemoryFactory) {
        var factory = {};
        var watched;

        factory.AddWatched = function(showId, showTitle, epiSeason, epiNr, epiTitle, showImage, watchedAt){
            if (!watched)
                watched = factory.GetWatched();

            watchedShow = $.grep(watched, function(item){
                return item.showId == showId;
            });

            if (watchedShow.length == 0){
                // newly show started
                watched.push({showId: showId, showTitle: showTitle, episodes: [{season: epiSeason, episode: epiNr, episodeTitle: epiTitle, showImage: showImage, watchedAt: watchedAt}] });
                MemoryFactory.SetValue("WatchedEpisodes", watched);
                sort();
            }
            else
            {
                // add to existing show
                epi = $.grep(watched, function(item){
                    return item.season == epiSeason && episode == epiNr;
                });
                if(epi.length > 0)
                    epi.watchedAt = watchedAt;
                else
                {
                    watchedShow[0].episodes.push({season: epiSeason, episode: epiNr, episodeTitle: epiTitle, showImage: showImage, watchedAt: watchedAt})
                    MemoryFactory.SetValue("WatchedEpisodes", watched);
                    sort();
                }
            }
        }

        factory.GetWatched = function(){
           if (!watched){
                watched = MemoryFactory.GetValue("WatchedEpisodes");
                if(!watched)
                    watched = [];
            }
            sort();
            return watched;
        }

        factory.GetWatchedForShow = function(showId){
            if (!watched)
                watched = factory.GetWatched();

            for(var i = 0 ; i < watched.length; i++){
                if(watched[i].showId == showId)
                    return watched[i].episodes;
            }
            return false;
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