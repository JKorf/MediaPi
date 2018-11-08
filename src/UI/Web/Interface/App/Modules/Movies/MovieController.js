(function () {

    angular.module('pi-test').controller('MovieController', function ($scope, $rootScope, $http, $timeout, $stateParams, HistoryFactory, ConfirmationFactory, CacheFactory) {
        $scope.selectedTorrent = { url: "" };

        Init();

        $scope.goToImdb = function(){
             window.open('http://www.imdb.com/title/' + $stateParams.id);
        }

        $scope.sortResolutions = function(torrent){
            return parseInt(torrent.quality.split("p")[0])
        }

        $scope.watchTrailer = function(){
            ConfirmationFactory.confirm_play().then(function(){
                $rootScope.$broadcast("startPlay", {title: $scope.movie.title, type: "YouTube"});
                $http.post("/youtube/play_youtube_url?url=" + encodeURIComponent($scope.movie.youtube_trailer) + "&title=" + encodeURIComponent($scope.movie.title + " trailer"));
            });
        }

        $scope.synopsisClick = function(){
            $(".movie-synopsis").removeClass('multiline-truncate');
        }

        $scope.selectTorrent = function(torrent){
            $scope.selectedTorrent.url = torrent.url;
        }

        $scope.watchMovie = function(){
            ConfirmationFactory.confirm_play().then(function(){
                $rootScope.$broadcast("startPlay", {title: $scope.movie.title, type: "Movie"});

                $http.post('/movies/play_movie?url=' + encodeURIComponent($scope.selectedTorrent.url) + '&id=' + $scope.movie.id + '&title=' + encodeURIComponent($scope.movie.title) + '&img=' + encodeURIComponent($scope.movie.poster));

                HistoryFactory.AddWatchedMovie($scope.movie.id, $scope.movie.title, encodeURIComponent($scope.movie.poster), new Date());
            });
        }

        function Init(){
            $scope.promise = CacheFactory.Get("/movies/get_movie?id="+$stateParams.id, 900).then(function (response) {
                $scope.movie = response;
                console.log($scope.movie);
                if($scope.movie.torrents.length > 0)
                {
                    for (var i = 0 ; i < $scope.movie.torrents.length ;i++){
                        if($scope.movie.torrents[i].quality == "1080p" || $scope.movie.torrents[i].quality == "1080"){
                            $scope.selectedTorrent.url = $scope.movie.torrents[i].url;
                            return;
                        }
                    }

                    for (var i = 0 ; i < $scope.movie.torrents.length ;i++){
                        if($scope.movie.torrents[i].quality == "720p" || $scope.movie.torrents[i].quality == "720"){
                            $scope.selectedTorrent.url = $scope.movie.torrents[i].url;
                            return;
                        }
                     }

                     for (var i = 0 ; i < $scope.movie.torrents.length ;i++){
                        if($scope.movie.torrents[i].quality == "480p" || $scope.movie.torrents[i].quality == "480"){
                            $scope.selectedTorrent.url = $scope.movie.torrents[i].url;
                            return;
                        }
                    }
                }
            }, function (err) {
                console.log(err);
            });
        }
    });

})();