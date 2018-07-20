(function () {

    angular.module('pi-test').controller('TorrentsController', function ($scope, $rootScope, $http, $state, CacheFactory, ConfirmationFactory) {
        $scope.search = "";
        $scope.torrents = [];
        $scope.done = false;

        $scope.watch = function(torrent){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/torrent/play_torrent?url=' + encodeURIComponent(torrent.url) + '&title=' + encodeURIComponent(torrent.title));
            });
        }

        $scope.searchTorrents = function(){
            $scope.done = false;
            $scope.promise = CacheFactory.Get('/torrent/search?keywords=' + encodeURIComponent($scope.search), 900).then(function (response) {
                $scope.torrents = response;
                $scope.done = true;
            });
        }

        function Init(){
            $scope.promise = CacheFactory.Get('/torrent/top', 900).then(function (response) {
                $scope.torrents = response;
                console.log($scope.torrents.length);
                console.log($scope.promise.$$state.status);
                $scope.done = true;
            });
        }

        Init();
    });

})();