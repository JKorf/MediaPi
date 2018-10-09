(function () {
    angular.module('pi-test').directive('slider', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                model: "=",
                obj: "=",
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
            link: function ($scope, element, attrs, ctrl) {
                $scope.text_value = $scope.text($scope.actualModel);
                var changing = false;

                $timeout(function(){
                    if($scope.tooltipBottom){
                        $(element).find(".slider-tooltip").css("margin-top", "24px");
                    }

                    $(element).find(".range-slider").on("touchstart mousedown", function(event){
                        changing = true;
                        $(element).find(".slider-tooltip").css("display", "block");
                        if($scope.onStartChange)
                            $scope.onStartChange($scope.obj, $scope.model);
                    });
                    $(element).find(".range-slider").on("touchend mouseup", function(event){
                        changing = false;
                        console.log("change from " + $scope.model + " to " + $scope.actualModel);

                        $scope.model = $scope.actualModel;

                        $(element).find(".slider-tooltip").css("display", "none");
                        if($scope.onEndChange)
                            $scope.onEndChange($scope.obj, $scope.model);
                    });

                    $scope.$watch("buffer", function(newv, oldv){
                        update_buffer(newv);
                    });

                    $scope.$watch("actualModel", function(newv, oldv) {
                         $scope.text_value = $scope.text($scope.actualModel);
                    });

                    $scope.$watch("model", function(newv, oldv){
                        if(!changing)
                            $scope.actualModel = newv;

                        update_buffer($scope.buffer);
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