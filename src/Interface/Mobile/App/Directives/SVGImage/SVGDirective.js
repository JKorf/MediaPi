(function () {
    angular.module('pi-test').directive('svgImage', function ($timeout, SVGFactory) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                $(element).load(function () {
                    SVGFactory.check(element);
                });
                element.bind('error', function (er) {
                });
            }
        };
    });
})();