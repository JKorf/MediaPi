(function () {

    angular.module('pi-test').controller('YouTubeChannelController', function ($scope, $rootScope, $http, $state, $stateParams, CacheFactory, FavoritesFactory, ConfirmationFactory, HistoryFactory) {
        $scope.favs = [];

        $scope.parseNumber = function(number)
        {
            number = parseInt(number);
            if(number > 1000000)
                return Math.round(number * 10 / 1000000) / 10 + "M";
            if(number > 1000)
                return Math.round(number * 10 / 1000) / 10 + "k";
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

        $scope.showDescription = function(evnt){
            $(evnt.target).removeClass("multiline-truncate");
        }

        $scope.watchVideo = function(media){
            ConfirmationFactory.confirm_play().then(function(){
                $rootScope.$broadcast("startPlay", {title: media.title, type: "YouTube"});
                HistoryFactory.AddWatchedYouTube(media.title, new Date())
                $http.post('/youtube/play_youtube?id=' + media.id+'&title=' + encodeURIComponent(media.title));
            });
        }

        $scope.isFavorite = function(){
            for(var i = 0 ; i < $scope.favs.length; i++)
                if($scope.favs[i].id == $stateParams.id)
                    return true;
            return false;
        }

        $scope.toggleFavorite = function(){
            if(!$scope.isFavorite())
                FavoritesFactory.Add($stateParams.id, "YouTube", $scope.channelInfo.title, $scope.channelInfo.thumbnail);
            else
                FavoritesFactory.Remove($stateParams.id);
        }

        function Init(){
            FavoritesFactory.GetAll().then(function(data) {
                $scope.favs = data;
            });

            var url = '/youtube/channel_info?id=' + $stateParams.id;
            $scope.promise = CacheFactory.Get(url, 900).then(function(response){
                $scope.channelInfo = response;
                console.log(response);
            }, function(er){
                console.log("rejected: " + er);
            });
        }

        Init();
    });

})();