(function () {
    angular.module('pi-test').directive('imageonload', function () {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                $(element).after("<div class='image-loading'><img src='Images/loader.gif' /></div>")

                element.bind('load', function () {
                    $(element).siblings('.image-loading').remove();
                });
                element.bind('error', function (er) {
                    console.log(er);
                });
            }
        };
    });
})();