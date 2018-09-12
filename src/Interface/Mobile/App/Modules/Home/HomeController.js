(function () {

    angular.module('pi-test').controller('HomeController', function ($scope, $rootScope, $http, $state, $timeout, ConfirmationFactory, UnfinishedFactory, HistoryFactory, FavoritesFactory, CacheFactory) {
        $scope.lastWatched = [];
        $scope.favorites = [];

        $scope.expandItem = function(evnt){
            $(evnt.srcElement).closest(".home-item").toggleClass("expanded");
            $(evnt.srcElement).closest(".home-item-bar").find(".home-item-down-icon").toggleClass("flipped");
        }

        $scope.addLeadingZero = function(val){
            if ((val+"").length == 1)
                return "0"+val;
            return val;
        }

        $scope.timeToTimespan = function(date){
            var time = new Date();
            deltaS = (time.getTime() - new Date(date).getTime()) / 1000;

            if (deltaS < 60)
                return 'just now';
            else if (deltaS < 3600)
                return Math.round((deltaS / 60)) + " mins ago";
            else if (deltaS < 86400)
                return Math.round((deltaS / 3600)) + " hours ago";
            else if (deltaS < 172800)
                return "yesterday";
            else
                return Math.round((deltaS / 86400)) + " days ago"
        }

        $scope.getFileName = function(url){
            url = url.substring(url.lastIndexOf("/")+ 1);
            return (url.match(/[^.]+(\.[^?#]+)?/) || [])[0];
        }

        $scope.goToFile = function(url){
            console.log(url);
            $state.go("hd", { path: url });
        }

        $scope.goToShow = function(id){
            $state.go("show", { id: id });
        }

        $scope.continue_torrent = function(uf){
            ConfirmationFactory.confirm_continue(uf.name).then(function(){
                var name = uf.name;
                if (!name)
                    name = uf.mediaFile;

                $rootScope.$broadcast("startPlay", {title: name, type: "Show"});
                $http.post("/movies/play_continue?type="+uf.type+"&url=" + encodeURIComponent(uf.url) + "&title=" + encodeURIComponent(uf.name) + "&image=" + encodeURIComponent(uf.image) + "&position=" + uf.position + "&mediaFile=" +encodeURIComponent(uf.mediaFile));
            });
        }

        $scope.remove_unfinished = function( uf){
            $scope.unfinished.splice($scope.unfinished.indexOf(uf), 1);
            UnfinishedFactory.Remove(uf);
        }

        Init();

        function Init(){
            UnfinishedFactory.GetUnfinished().then(function(data){
                $(".unfinished-list .home-list-loader").remove();
                if(data.length > 0){
                    data.sort(function(a, b) {
                        a = new Date(a.watchedAt);
                        b = new Date(b.watchedAt);
                        return a>b ? -1 : a<b ? 1 : 0;
                    });
                }
                $scope.unfinished = data;
            });

            HistoryFactory.GetWatched().then(function(data){
                $scope.history = data;
                console.log(data);
            });

            var favs = FavoritesFactory.GetAll().then(function(favs){
                if (favs.length == 0){
                     $(".favorites-list .home-list-loader").remove();
                     $(".favorites-list .list-no-items").css("display", "block");
                 }

                for(var i = 0 ; i < favs.length ; i++){
                    CacheFactory.Get('/shows/get_show?id=' + favs[i], 900).then(function (response) {
                        $(".favorites-list .home-list-loader").remove();
                        DetermineLastEpisodeRelease(response);
                        $scope.favorites.push(response);
                    }, function (er) {
                        console.log(er);
                    });
                }
            });
        }

        function DetermineLastEpisodeRelease(show){
        return;
            var lastWatchedShowEpisode;
            show.toWatch = 0;
            for(var i = 0; i < $scope.watchedEpisodes.length; i++){
                if($scope.watchedEpisodes[i].showId == show._id){
                    var lastEpi;
                    for(var i2 = 0; i2 < $scope.watchedEpisodes[i].episodes.length; i2++){
                        var testEpi = $scope.watchedEpisodes[i].episodes[i2];
                        if(!lastEpi)
                            lastEpi = testEpi;
                        else
                        {
                            if(testEpi.season > lastEpi.season || (testEpi.season == lastEpi.season && testEpi.episode > lastEpi.episode))
                            {
                                lastEpi = testEpi;
                            }
                        }
                    }
                    lastWatchedShowEpisode = lastEpi;
                    break;
                }
            }

            if(!lastWatchedShowEpisode)
            {
                show.toWatch = show.episodes.length;
                return;
            }

            for(var i = 0; i < show.episodes.length; i++){
                if(show.episodes[i].season > lastWatchedShowEpisode.season)
                    show.toWatch += 1;
                else if(show.episodes[i].season == lastWatchedShowEpisode.season && show.episodes[i].episode > lastWatchedShowEpisode.episode)
                    show.toWatch += 1;
            }
        }
    });

})();