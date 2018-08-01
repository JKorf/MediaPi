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
                            $scope.onStartChange();
                    });
                    $(element).find(".range-slider").on("touchend mouseup", function(event){
                        changing = false;

                        // split by . to split by objects
                        var split = attrs.model.split(".");
                        // start searching for right scope at parent scope since it's never this scope
                        var obj = $scope.$parent;
                        if(split.length > 1)
                        {
                            for(var i = 0; i < split.length - 1; i++){
                                obj = obj[split[i]];
                            }
                        }
                        obj[split[split.length-1]] = $scope.actualModel;

                        $(element).find(".slider-tooltip").css("display", "none");
                        if($scope.onEndChange)
                            $scope.onEndChange();
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