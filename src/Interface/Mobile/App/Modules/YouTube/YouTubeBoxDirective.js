(function () {
    angular.module('pi-test').directive('youtubeBox', function ($rootScope, $state) {
        return {
            restrict: 'E',
            scope: {
                item: '='
            },
            templateUrl: '/App/Modules/YouTube/youtubebox.html',
            link: function ($scope, element, attrs) {
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
            }
        }
    });
})();