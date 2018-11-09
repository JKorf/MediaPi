(function () {
    angular.module('pi-test').directive('progressBar', function ($rootScope, $state, $timeout) {
        return {
            restrict: 'E',
            scope: {
                percentage: "=",
                text: "@",
            },
            templateUrl: '/App/Directives/ProgressBar/progressbar.html',
            link: function ($scope, element, attrs) {
                $scope.$watch("percentage", function(newv, oldv){
                    var bar = $(element).find(".progress-bar-bar")
                    var text = $(element).find(".progress-bar-text")

                    bar.css("width", $scope.percentage + "%");

                    $timeout(function(){
                        var textLength = stringLength($scope.text);
                        var dif = textLength - bar[0].scrollWidth
                        if(dif > -8)
                        {
                            text.css("left", $scope.percentage +"%");
                            text.css("max-width", "calc(" + (100 - $scope.percentage) + "% - 8px)");
                        }
                        else{
                            text.css("max-width", $scope.percentage + "%");
                            text.css("left", "4px");
                        }
                    });
                });

                function stringLength(text){
                      this.e = document.createElement('span');
                      this.e.style.fontSize = "15px";
                      this.e.style.fontFamily = "Geneva, Tahoma, Verdana, sans-serif";
                      this.e.innerHTML = text;
                      document.body.appendChild(this.e);
                      var w = this.e.offsetWidth;
                      document.body.removeChild(this.e);
                      return w;
                }
            }
        };
    });
})();