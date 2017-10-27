(function () {
    angular.module('pi-test').directive('ripple', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'A',
            link: function ($scope, element, attrs) {
                $(element).click(function(e){
                    var ripple = $("<div class='ripple-outer'><div class='ripple' style='left: "+(e.offsetX-5)+"px; top: "+(e.offsetY-5)+"px'></div></div>");
                    $(element).append(ripple);
                    $timeout(function(){
                        rippleInner = ripple.find(".ripple");
                        rippleInner.css("opacity", "0");
                        rippleInner.css("width", "100px");
                        rippleInner.css("height", "100px");
                        rippleInner.css("left", e.offsetX - 50+"px");
                        rippleInner.css("top", e.offsetY - 50+"px");
                        $timeout(function(){
                            ripple.remove();
                        }, 1000);
                    }, 30);
                });
            }
        };
    });
})();