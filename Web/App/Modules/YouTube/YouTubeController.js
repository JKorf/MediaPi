(function () {

    angular.module('pi-test').controller('YouTubeController', function ($scope, $rootScope, $http, $state, ConfirmationFactory, CacheFactory) {
        var videosPerPageLocal = 10;
        var videosPerPageServer = 50;
        var dirty = false;

        $scope.localPage = 0;
        $scope.serverPage = -1;

        $scope.done = false;
        $scope.videos = [];
        $scope.search = {
            keywords: ""
        }

        Init();

        $scope.nextPage = function(){
            $scope.localPage++;
            $('.view').scrollTop(0);
            GetVideos($scope.localPage);
        }

        $scope.prevPage = function(){
            $scope.localPage--;
            $('.view').scrollTop(0);
            GetVideos($scope.localPage);
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

        $scope.parseYoutubeLength = function(length){
            var lengthWithoutPrefix = length.substr(2);
            if (length.indexOf("M") != -1){
                var minutes = lengthWithoutPrefix.split("M")[0];
                var seconds = lengthWithoutPrefix.split("M")[1].split("S")[0];
            }else{
                var seconds = lengthWithoutPrefix.split("S")[0];
                var minutes = 0;
            }
            if (seconds == '')
                seconds = '00';

            if (seconds.length == 1)
                seconds = '0' + seconds;

            return minutes + ":" + seconds;
        }

        $scope.orderByDate =  function(item) {
            var parts = item.uploaded.split('T')
            var dateParts = parts[0].split('-');
            var timeParts = parts[1].split('.')[0].split(':');
            var date = new Date(parseInt(dateParts[0]),
                                parseInt(dateParts[1]),
                                parseInt(dateParts[2]),
                                parseInt(timeParts[0]),
                                parseInt(timeParts[1]),
                                parseInt(timeParts[2]));

            return date;
        };

        $scope.watchVideo = function(video){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/youtube/play_youtube?id=' + video.id+'&title=' + encodeURIComponent(video.title));
            });
        }

        $scope.searchVideos = function(){
            $(".youtube-search-box input").blur();

            if($scope.search.keywords.length == 0){
                Init();
                return;
            }

            $scope.promise = $http.get( '/youtube/search?query=' + encodeURIComponent($scope.search.keywords)).then(function (response) {
                $scope.done = true;
                $scope.videos = response.data;
                console.log($scope.videos);
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }

        function Init(){
            GetVideos($scope.localPage);
        }

        function GetVideos(localPage){
            if(dirty)
            {
                $scope.videos = [];
                $scope.localPage = 0;
                $scope.serverPage = 0;
                dirty = false;
            }
            else
            {
                var newServerPage = LocalPageToServerPage(localPage);
                if(newServerPage == $scope.serverPage)
                    return;
            }

            $scope.serverPage = LocalPageToServerPage(localPage);
            console.log($scope.serverPage);
            if($scope.videos[$scope.serverPage])
                return;

            var baseUri = '/youtube/subscription_feed?page=' + ($scope.serverPage + 1);
            $scope.done = false;
            $(".youtube-search-box input").blur()
            console.log("Getting new videos");

            $scope.promise = CacheFactory.Get(baseUri, 900).then(function (response) {
                $scope.done = true;
                $scope.videos[$scope.serverPage] = response;
                console.log($scope.videos);
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }

        function LocalPageToServerPage(localPage){
            var videosStart = localPage * videosPerPageLocal;
            var serverPage = Math.floor(videosStart / videosPerPageServer);
            return serverPage;
        }

    });

})();