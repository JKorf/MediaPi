(function () {

    angular.module('pi-test').controller('DebugController', function ($scope, $rootScope, $http, $state, $interval, $timeout, ErrorFactory, CacheFactory, MemoryFactory) {
        var debugInterval;
        var infoInterval;
        var errors;
        var request;
        var requestInfo;

        var minutes = 60;
        var hours = minutes*60;
        var days = hours * 24;
        var weeks = days * 7;

        $scope.tab = 'info';
        $scope.errorHeight = 0;

        Init();

        $scope.$on("$destroy", function(){
            $interval.cancel(debugInterval);
            $interval.cancel(infoInterval);
        })

        $scope.switchTab = function(tab){
            $scope.tab = tab
        }

        $scope.write_big_number = function(numb){
            if (!numb)
                return numb;

            if (numb > 10000)
                return (numb / 1000).toFixed(1) + "k";
            return numb;
        }

        $scope.resetCache = function(){
            if (confirm('Are you sure you want to clear the cache?')) {
                CacheFactory.Clear();
                MemoryFactory.Clear();
            }
        }

        $scope.to_time = function(val){
            result = "";
            var daysReached = false;
            if (!val || val == "")
                return val;

            seconds = val / 1000;

            if(seconds > days){
                result += Math.floor(seconds / days) + " days, ";
                seconds = seconds % days;
                daysReached = true;
            }

            if(seconds > hours){
                result += Math.floor(seconds / hours) + " hours, ";
                seconds = seconds % hours;
            }

            if (!daysReached){
                result += Math.floor(seconds / minutes) + " mins, ";
            }
            return result.slice(0, -2)
        }

        function Init(){
            $http.get('/util/version').then(function(response){
                $scope.version = response.data;
            }, function(er){
                console.log(er);
            });

            $scope.errors = ErrorFactory.getErrors();
            ErrorFactory.onNewError(function(){
                $scope.errors = ErrorFactory.getErrors();
            });

            RequestDebug();
            RequestInfo();

            debugInterval = $interval(function(){
                RequestDebug();
            }, 2000);

            infoInterval = $interval(function(){
                RequestInfo();
            }, 5000);
        }

        function RequestInfo(){
            requestInfo = $http.get("/util/info").then(function(response){
                requestInfo = false;
                $scope.info = response.data;
            }, function(er){
                $scope.info = false;
            });
        }

        function RequestDebug(){
            if(request)
                return;

            request = $http.get("/util/debug").then(function(response){
                request = false;
                $scope.debugInfo = response.data;

                if ($scope.debugInfo.torrent_state == 1)
                    $scope.debugInfo.torrent_state = "Initial";
                if ($scope.debugInfo.torrent_state == 2)
                    $scope.debugInfo.torrent_state = "Downloading metadata";
                if ($scope.debugInfo.torrent_state == 3)
                    $scope.debugInfo.torrent_state = "Downloading";
                if ($scope.debugInfo.torrent_state == 4)
                    $scope.debugInfo.torrent_state = "Paused";
                if ($scope.debugInfo.torrent_state == 5)
                    $scope.debugInfo.torrent_state = "Done";
            }, function(er){
                request = false;
                $scope.debugInfo = false;
            });
        }
    });
})();