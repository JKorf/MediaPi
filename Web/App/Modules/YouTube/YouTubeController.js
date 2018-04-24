(function () {

    angular.module('pi-test').controller('YouTubeController', function ($scope, $rootScope, $http, $state, ConfirmationFactory, CacheFactory) {
        $scope.done = false;
        $scope.videos = [];
        $scope.channels = [];
        $scope.active = "home";

        $scope.search = {
            keywords: ""
        }

        Init();

        $scope.goHome = function(){
            $scope.active = "home";
            $scope.videos = [];
            $scope.channels = [];
            GetVideos();
        }

        $scope.goChannels = function(){
            $scope.active = "channels";
            $scope.done = false;
            $scope.videos = [];
            $scope.channels = [];
            $scope.promise = $http.get( '/youtube/channels').then(function (response) {
                $scope.done = true;
                console.log(response.data);
                $scope.channels = response.data;
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }

        $scope.goSearch = function(){
            $scope.active = "search";
            $(".youtube-search-box input").focus();
        }

        $scope.search = function(){
            $scope.videos = [];
            $scope.done = false;
            $scope.channels = [];
            $scope.promise = $http.get( '/youtube/search?query=' + encodeURIComponent($scope.search.keywords)).then(function (response) {
                $scope.active = "search-result"
                $scope.done = true;
                console.log(response.data);
                $scope.videos = response.data.videos;
                $scope.channels = response.data.channels;
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
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

        $scope.openChannel = function(channel){
            $scope.videos = [];
            $scope.channels = [];
            $scope.promise = $http.get( '/youtube/channel_feed?id=' + channel.id).then(function (response) {
                $scope.done = true;
                console.log(response.data);
                $scope.videos = response.data;
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }

        $scope.watchVideo = function(video){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/youtube/play_youtube?id=' + video.id+'&title=' + encodeURIComponent(video.title));
            });
        }

        function Init(){
            GetVideos();
        }

        function GetVideos(){
            var baseUri = '/youtube/home?page=' + ($scope.serverPage + 1);
            $scope.done = false;
            $(".youtube-search-box input").blur()
            console.log("Getting new videos");

            $scope.promise = CacheFactory.Get(baseUri, 900).then(function (response) {
                $scope.done = true;
                $scope.videos = response.videos;
                $scope.channels = response.channels;
                console.log(response);
            }, function (err) {
                $scope.done = true;
                console.log(err);
            });
        }
    });

})();