(function () {

    angular.module('pi-test').factory('ConfirmationFactory', function ($rootScope, $q) {
        var factory = {};

        factory.confirm_play = function(){
            var defer = $q.defer();

            if($rootScope.playerState == 'disconnected'){
                $rootScope.openPopup();
                $rootScope.setPopupContent("Not connected to server", false, true, true, "Unable to start because there is no connection to the server", $rootScope).then(function(){
                    defer.reject();
                }, function(){
                    defer.reject();
                });
            }
            else if($rootScope.playerState != 'Nothing'){
                $rootScope.openPopup();
                $rootScope.setPopupContent("Cancel current media", true, true, true, "Do you want to cancel the current media?", $rootScope).then(function(){
                    defer.resolve();
                }, function(){
                    defer.reject();
                });
            }
            else
                defer.resolve();
            return defer.promise;
        }

        factory.confirm_subtitle = function(){
            var defer = $q.defer();

            $rootScope.openPopup();
            $rootScope.setPopupContent("Add subtitle", true, true, true, "Do you want to add the subtitle the current media?", $rootScope).then(function(){
                defer.resolve();
            }, function(){
                defer.reject();
            });

            return defer.promise;
        }

        factory.confirm_stop_current_media = function(){
            var defer = $q.defer();

            $rootScope.openPopup();
            $rootScope.setPopupContent("Stop current media", true, true, true, "Do you want to stop the current media?", $rootScope).then(function(){
                defer.resolve();
            }, function(){
                defer.reject();
            });

            return defer.promise;
        }

        return factory;
    });

})();