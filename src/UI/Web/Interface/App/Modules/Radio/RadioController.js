(function () {

    angular.module('pi-test').controller('RadioController', function ($scope, $rootScope, $http, $state, ConfirmationFactory) {
        Init();

        $scope.playRadio = function(radio){
            ConfirmationFactory.confirm_play().then(function(){
                $http.post('/radio/play_radio?id='+radio.id);
            });
        }

        function Init(){
            $scope.promise = $http.get('/radio/get_radios').then(function(result){
                $scope.radios = result.data;
                console.log($scope.radios);
            }, function(er){
                console.log(er);
            });
        }
    });

})();