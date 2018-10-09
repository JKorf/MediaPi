(function () {

    angular.module('pi-test').controller('LightingController', function ($scope, $http) {
        $scope.devices = [];

         function Init(){
             $http.post("/lighting/debug");
             $http.get("/lighting/get_lights").then(function(data){
                 console.log(data);
                 $scope.devices = data.data;

                 if($scope.devices.length == 0)
                    SetTestData();
             }, function(e){
                SetTestData();
             });
         }

         function SetTestData(){
            $scope.devices =
            [
                {
                    index: 0,
                    application_type: 1,
                    last_seen: 1538726737,
                    reachable: true,
                    lights: [
                        {
                            supports_dimmer: true,
                            supports_temp: true,
                            supports_color: false,
                            state: true,
                            dimmer: 200,
                            color_temp: 260,
                            hex_color: ""
                        }
                    ]
                },
                {
                    index: 1,
                    application_type: 2,
                    last_seen: 1538726737,
                    reachable: true,
                    lights: [
                        {
                            supports_dimmer: true,
                            supports_temp: true,
                            supports_color: true,
                            state: false,
                            dimmer: 100,
                            color_temp: 360,
                            hex_color: "4a418a"
                        }
                    ]
                }
            ];
         }

         $scope.dimmerToolTip = function(value){
             var min = 0;
             var max = 254;
            return Math.round((value - min) / (max - min) * 100) + "%";
         }

         $scope.warmthToolTip = function(value){
             var min = 250;
             var max = 454;
            return Math.round((value - min) / (max - min) * 100) + "%";
         }

         $scope.switchGroup = function(group)
         {
             if(group.state)
                $http.post("/lighting/switch_light?index="+group.index+"&state=on");
             else
                $http.post("/lighting/switch_light?index="+group.index+"&state=off");
         };

         $scope.dimmerGroup = function(group, amount){
              $http.post("/lighting/dimmer_light?index="+group.index+"&dimmer=" + amount);
         }

         $scope.warmthGroup = function(group, amount){
              $http.post("/lighting/warmth_light?index="+group.index+"&warmth=" + amount);
         }

         Init();
    });
})();