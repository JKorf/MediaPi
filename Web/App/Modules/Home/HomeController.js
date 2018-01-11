﻿(function () {

    angular.module('pi-test').controller('HomeController', function ($scope, $rootScope, $http, $state, $timeout, EpisodesWatchedFactory, FilesWatchedFactory, FavoritesFactory, CacheFactory) {
        $scope.lastWatched = [];
        $scope.favorites = [];

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
                return Math.round((deltaS / 60)) + " minutes ago";
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
            url = url.substring(0, url.lastIndexOf("/") + 1);
            console.log(url);
            $state.go("hd", { path: url });
        }

        $scope.goToShow = function(id){
            $state.go("show", { id: id });
        }

        Init();

        function Init(){
            $scope.watchedEpisodes = EpisodesWatchedFactory.GetWatched();
            var favs = FavoritesFactory.GetAll().then(function(favs){
                console.log("Init favs home");
                    console.log(favs);

                for(var i = 0 ; i < favs.length ; i++){
                    CacheFactory.Get('/shows/get_show?id=' + favs[i], 900).then(function (response) {
                        DetermineLastEpisodeRelease(response);
                        $scope.favorites.push(response);
                    }, function (er) {
                        console.log(er);
                    });
                }
            });

            var watchedFiles = FilesWatchedFactory.GetWatchedFiles();
            if(watchedFiles.length > 0){
                watchedFiles.sort(function(a, b) {
                    a = new Date(a.watchedAt);
                    b = new Date(b.watchedAt);
                    return a>b ? -1 : a<b ? 1 : 0;
                });
            }
            $scope.lastWatchedFiles = watchedFiles;

            $timeout(function(){
                var elem3 = $(".favorites");
                elem3.scroll(function(){
                    if (elem3[0].scrollWidth - elem3.scrollLeft() == elem3.outerWidth())
                        $(elem3).siblings(".list-more-fade").hide();
                    else
                        $(elem3).siblings(".list-more-fade").show();
                });

                var elem2 = $(".last-watched-files");
                elem2.scroll(function(){
                    if (elem2[0].scrollWidth - elem2.scrollLeft() == elem2.outerWidth())
                        $(elem2).siblings(".list-more-fade").hide();
                    else
                        $(elem2).siblings(".list-more-fade").show();
                });
            }, 10);
        }

        function DetermineLastEpisodeRelease(show){
            var lastWatchedShowEpisode;
            show.toWatch = 0;
            for(var i = 0; i < $scope.watchedEpisodes.length; i++){
                if($scope.watchedEpisodes[i].showId == show._id){
                    var lastEpi;
                    for(var i2 = 0; i2 < $scope.watchedEpisodes[i].episodes.length; i2++){
                        if(!lastEpi)
                            lastEpi = $scope.watchedEpisodes[i].episodes[i2];
                        else{
                            if($scope.watchedEpisodes[i].episodes[i2].watchedAt > lastEpi.watchedAt)
                                lastEpi = $scope.watchedEpisodes[i].episodes[i2];
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