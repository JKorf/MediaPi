(function () {

    angular.module('pi-test').controller('SettingsController', function ($scope, $rootScope, $http, $state) {
        Init();

        $scope.saveSettings = function(){
            $http.post("/util/save_settings?" +
            "raspberry=" + $scope.settings.raspberry +
            "&gui=" + $scope.settings.gui +
            "&external_trackers=" + $scope.settings.external_trackers +
            "&max_subs=" + $scope.settings.max_sub_files);

            if(confirm("The changes will only take effect after restarting the media player. Do you wish to restart now?")){
                $http.post('/util/restart_app');
            }
        }

        function Init(){
            $scope.promise = $http.get('/util/get_settings').then(function(result){
                $scope.settings = result.data;
                console.log($scope.settings);
            }, function(er){
                console.log(er);
            });
        }

    });

})();