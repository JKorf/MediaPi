(function () {
    angular.module('pi-test').directive('slider', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                model: "=",
                text: "=",
                min: "@",
                max: "@",
                step: "@",
                buffer: "=",
                onStartChange: "=",
                onEndChange: "=",
                tooltipBottom: "="
            },
            templateUrl: '/App/Directives/Slider/slider.html',
            link: function ($scope, element, attrs) {
                $scope.text_value = $scope.text($scope.value);

                $timeout(function(){
                    if($scope.tooltipBottom){
                        $(element).find(".slider-tooltip").css("margin-top", "24px");
                    }
                    $(element).find(".range-slider").on("touchstart mousedown", function(event){
                        $(element).find(".slider-tooltip").css("display", "block");
                        if($scope.onStartChange)
                            $scope.onStartChange();
                    });
                    $(element).find(".range-slider").on("touchend mouseup", function(event){
                        $(element).find(".slider-tooltip").css("display", "none");
                        if($scope.onEndChange)
                            $scope.onEndChange();
                    });

                    $scope.$watch("buffer", function(newv, oldv){
                        update_buffer(newv);
                    });

                    $scope.$watch("model", function(newv, oldv){
                        update_buffer($scope.buffer);
                        $scope.text_value = $scope.text($scope.model);
                    });
                }, 10);

                function update_buffer(buffer){
                    var sliderWidth = $(element).find(".range-slider").innerWidth();
                    var thumb = parseFloat($scope.model) / ($scope.max - $scope.min);
                    var startPosition = (sliderWidth * thumb) + (15 * (1 - thumb));
                    var width = sliderWidth * (buffer / parseFloat(100))
                    if(sliderWidth - (startPosition + width) < 5 || startPosition + width > sliderWidth)
                        width = sliderWidth - startPosition;

                    $(element).find(".slider-buffer").css("left", startPosition + "px");
                    $(element).find(".slider-buffer").css("width", (width)+ "px");
                }
            }
        };
    });
})();