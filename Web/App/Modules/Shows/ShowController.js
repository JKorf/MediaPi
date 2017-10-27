﻿(function () {

    angular.module('pi-test').controller('ShowController', function ($scope, $rootScope, $http, $stateParams, $timeout, $state, EpisodesWatchedFactory, ConfirmationFactory, FavoritesFactory, CacheFactory) {

        $scope.selectedResolution = { resolution: '720p' };
        $scope.selectedSeason;
        $scope.selectedEpisode;

        $scope.keys = function(obj){
          return obj? Object.keys(obj) : [];
        }

        $scope.sortResolutions = function(res){
            return parseInt(res.split("p")[0])
        }

        $scope.goToImdb = function(){
            window.open('http://www.imdb.com/title/' + $stateParams.id);
        }

        $scope.synopsisClick = function(){
            $(".show-synopsis").removeClass('multiline-truncate');
        }

        $scope.showFullEpisodeOverview = function($event){
            $($event.currentTarget).removeClass('multiline-truncate');
        }

        $scope.selectSeason = function(season){
            $scope.selectedSeason = season;
        }

        $scope.selectEpisode = function(episode){
            if(episode == $scope.selectedEpisode)
            {
                $scope.selectedEpisode = null;
                return;
            }
            $scope.selectedEpisode = episode;
            selectHighestRes(episode);
        }

        $scope.selectResolution = function(res){
            console.log(res);
            $scope.selectedResolution.resolution = res;
        }

        $scope.downloadEpisode = function(episode){
             $http.post('/torrents/download?url=' + encodeURIComponent(episode.torrents[$scope.selectedResolution.resolution].url) + '&title=' + encodeURIComponent($scope.show.title));

             $(".show-wrapper").append("<div class='download-started'><img src='/Images/download-blue.png' /></div>")
            $timeout(function(){
                $(".download-started").css("opacity", "0");
                $(".download-started").css("width", "10px");
                $(".download-started").css("height", "10px");
                $(".download-started").css("left", "calc(50% - 10px)");
                $(".download-started").css("top", "calc(50% - 10px)");
                $timeout(function(){
                    $(".download-started").remove();
                }, 1000)
            });
        }

        $scope.watchEpisode = function(episode){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/shows/play_episode?url=' + encodeURIComponent(episode.torrents[$scope.selectedResolution.resolution].url) + '&title=' + encodeURIComponent($scope.show.title) + '&img=' + encodeURIComponent($scope.show.images.poster));

                EpisodesWatchedFactory.AddWatched($scope.show._id, $scope.show.title, episode.season, episode.episode, episode.title, $scope.show.images.poster, new Date());
                $scope.watched = EpisodesWatchedFactory.GetWatchedForShow($stateParams.id);
            });
        }

        $scope.isFavorite = function(){
            return FavoritesFactory.IsFavorite($stateParams.id);
        }

        $scope.toggleFavorite = function(){
            console.log($stateParams.id);
            if(!FavoritesFactory.IsFavorite($stateParams.id))
            {
                FavoritesFactory.Add($stateParams.id);
            }else{
                FavoritesFactory.Remove($stateParams.id);
            }
        }

        $scope.isWatched = function(epi){
            for(var i = 0; i < $scope.watched.length; i++){
                if($scope.watched[i].season == epi.season &&
                   $scope.watched[i].episode == epi.episode)
                   return true;
            }
            return false;
        }

        Init();

        function Init(){
            var url = '/shows/get_show?id=' + $stateParams.id;
            $scope.promise = CacheFactory.Get(url, 900).then(function(response){
                $scope.show = response;
                OrderEpisodes();
            }, function(er){
                console.log("rejected: " + er);
            });

            $scope.watched = EpisodesWatchedFactory.GetWatchedForShow($stateParams.id);
        }

        function selectHighestRes(episode){
            var keys = Object.keys(episode.torrents);
            for(var i2 = 0; i2 < keys.length; i2++){
                if(keys[i2] == "1080" || keys[i2] == "1080p"){
                    $scope.selectedResolution = { resolution: keys[i2] };
                    return;
                }
            }
            for(var i2 = 0; i2 < keys.length; i2++){
                if(keys[i2] == "720" || keys[i2] == "720p"){
                    $scope.selectedResolution = { resolution: keys[i2] };
                    return;
                }
            }
            for(var i2 = 0; i2 < keys.length; i2++){
                if(keys[i2] == "480" || keys[i2] == "480p"){
                    $scope.selectedResolution = { resolution: keys[i2] };
                    return;
                }
            }
        }

        function OrderEpisodes() {
            $scope.show.Seasons = [];
            $scope.show.episodes.sort(function(a, b){return a.season-b.season});

            var curSeason = -1;
            var seasonIndex = -1;
            for (var i = 0; i < $scope.show.episodes.length; i++) {
                var epi = $scope.show.episodes[i];
                var season = epi.season;

                if (curSeason != season) {
                    curSeason = season;
                    seasonIndex++;
                    $scope.show.Seasons[seasonIndex] = [];
                }

                $scope.show.Seasons[seasonIndex].push(epi);
            }

            for(var i = 0 ; i < $scope.show.Seasons.length; i++)
            {
                $scope.show.Seasons[i].sort(function(a, b)
                {
                    return a.episode - b.episode;
                });
            }

            if($scope.show.Seasons.length == 1)
                $scope.selectedSeason = $scope.show.Seasons[0];

            console.log($scope.show);
        }
    });

})();