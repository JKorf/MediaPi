(function () {
    angular.module('pi-test').directive('imageonload', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                $(element).after("<div class='image-loading'><img src='Images/loader.gif' /></div>")
                $timeout(function(){
                    $(element).siblings(".image-loading").css("min-height", $(element).parent().parent().parent().css("min-height"));
                });

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