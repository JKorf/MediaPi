(function () {
    angular.module('pi-test').directive('swipe', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'A',
             scope: {
                onSwipe: "=",
                swipeItem: "=",
                swipeRemoveElement: "@"
            },
            link: function ($scope, element, attrs) {
                var total = 0;
                var start = 0;
                var startY = 0;
                var prev = 0;
                var down = false;
                $(element).on("touchstart", function(e){
                    start = e.originalEvent.targetTouches[0].clientX;
                    startY = e.originalEvent.targetTouches[0].clientY;
                    prev = start;
                    down = true;
                });

                $(element).on("touchmove", function(e){
                    if(!down)
                        return;

                    var dif = e.originalEvent.targetTouches[0].clientX - prev;
                    total += dif;
                    if(total < 0)
                        total = 0;
                    prev = e.originalEvent.targetTouches[0].clientX;

                    if(total < 30)
                        return;

                    $(element).css("left", total + "px");
                    $(element).css("right", "-" + (total) + "px");

                });

                $(element).on("touchend", function(e){

                    down = false;
                    $(element).css("transition", "left 0.4s ease, right 0.4s ease");

                    if(total > 120){
                        $timeout(function(){
                            $(element).css("min-width", $(element).width() + "px");
                            $(element).css("left", screen.width + "px");
                            $(element).css("right", screen.width + "px");
                        });

                        $timeout(function(){
                            $(element).closest("." + $scope.swipeMoveElement).remove();
                            $scope.onSwipe($scope.swipeItem);
                        }, 400);
                    }else{
                        $(element).css("left", "0px");
                        $(element).css("right", "0px");
                    }
                    total = 0;
                    start = 0;
                    prev = 0;
                    $timeout(function(){
                        $(element).css("transition", "left 0s, right 0s ease");
                    }, 100);
                });
            }
        };
    });
})();