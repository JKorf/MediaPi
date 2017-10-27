(function () {
    angular.module('pi-test').directive('slidingText', function ($rootScope, $state, $interval, $timeout) {
        return {
            restrict: 'A',
            scope: {
                text: "@",
                transtime: "@",
                intervaltime: "@"
            },
            link: function ($scope, element, attrs) {
                var slideInterval;

                $scope.$watch('text', function(newv, oldv) {
                   if(newv){
                        startAnimation();
                   }
                });

                $scope.$on("$destroy", function(){
                    if (slideInterval){
                        $interval.cancel(slideInterval);
                    }
                })

                function startAnimation(){
                    $(element).html("<div class='scrolltainer'><span>" + $scope.text + "</span></div>");
                    var scrolltainer = $(element).children('.scrolltainer');
                    var span = scrolltainer.children('span');

                    $(element).css("overflow", "hidden");
                    scrolltainer.css("height", "20px");
                    scrolltainer.css("transition", "margin-left " + $scope.transtime + " linear");
                    span.css("white-space", "nowrap");
                    var width = span.width();
                    var totalWidth = $(element).width();

                    if(width > totalWidth){
                        $timeout(function(){
                            scroll(scrolltainer, width-totalWidth)
                            slideInterval = $interval(function(){
                                scroll(scrolltainer, width-totalWidth);
                            } ,$scope.intervaltime);
                        }, 1000);
                    }
                }

                function scroll(scrolltainer, marg){
                    if(scrolltainer.css("margin-left") == "0px"){
                        scrolltainer.css("margin-left", "-" + marg + "px");
                    }else{
                        scrolltainer.css("margin-left", "0px");
                    }
                }
            }
        };
    });
})();