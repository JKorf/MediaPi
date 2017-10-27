(function () {
    angular.module('pi-test').directive('protectedImg', function ($rootScope, $state, $http, $timeout, CacheFactory) {
        return {
            restrict: 'E',
            scope: {
                src: "=",
                imgclass: "@"
            },
            templateUrl: '/App/Directives/ProtectedImg/protected-img.html',
            link: function ($scope, element, attrs) {

                $scope.$watch('src', function(newv, oldv){
                    if(newv){
                        var cached = CacheFactory.GetCached(newv, 86400); // Caching for a day
                        if(cached){
                            $scope.imgData = cached;
                            return;
                        }

                        $http({
                            method: 'GET',
                            url: '/util/get_protected_img?url=' + encodeURIComponent($scope.src),
                            responseType: 'arraybuffer'
                          }).then(function(response) {
                            $scope.imgData = arrayBufferToBase64(response.data);
                            CacheFactory.Cache(newv, $scope.imgData);
                          }, function(response) {
                            console.error('error in getting protected img.');
                          });
                    }
                });


                function arrayBufferToBase64(buffer) {
                    var binary = '';
                    var bytes = new Uint8Array(buffer);
                    var len = bytes.byteLength;
                    for (var i = 0; i < len; i++) {
                        binary += String.fromCharCode(bytes[i]);
                    }
                    return window.btoa(binary);
                }
            }
        };
    });
})();