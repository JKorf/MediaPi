(function () {
    angular.module('pi-test').directive('colorIndicator', function () {
        return {
            restrict: 'A',
            scope: {
                val: "="
            },
            link: function ($scope, element, attrs) {
                $(element).css('color', getColorString($scope.val, attrs.type));

                $scope.$watch('val', function(newv, oldv){
                    if(newv){
                        $(element).css('color', getColorString(newv, attrs.type));
                    }
                });

                function getColorString(input, type){
                    if(!input)
                        return;

                    var a = input/100;
                    if(type == 'grade')
                        a = input / 10;


                    var b = 120*a;
                    return 'hsl('+b+',100%,35%)'
                }
            }
        };
    });
})();