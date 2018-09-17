(function () {

    angular.module('pi-test').controller('SettingsController', function ($scope, $rootScope, $http, $state, MemoryFactory) {

        $scope.themes = [
            { name:"Default", file: "default" },
            { name:"Dark", file: "dark" }
        ];

        $scope.themeChanged = function(){
            MemoryFactory.SetValue("skin", $scope.selectedTheme.file);
            less.modifyVars({
              skin:  $scope.selectedTheme.file
            });
        }

        function Init(){
            var val = MemoryFactory.GetValue("skin");
            if (!val)
            {
                $scope.selectedTheme = $scope.themes[0];
                return;
            }

            for(var i = 0; i < $scope.themes.length; i++){
                if ($scope.themes[i].file == val)
                    $scope.selectedTheme = $scope.themes[i];
            }
        }

        Init();
    });

})();