(function () {

    angular.module('pi-test').controller('LightingController', function ($scope, $http, MemoryFactory, RequestFactory) {
        $scope.devices = [];
        $scope.editing = -1;
        $scope.colorPickerSettings = {
            position: 'top left'
          };

         function Init(){
            var requestInterval = RequestFactory.StartRequesting("/lighting/get_lights", 5000, ProcessData, SetTestData);
            RequestFactory.InvokeNow(requestInterval);
            $scope.$on('$destroy', function() {
                RequestFactory.StopRequesting(requestInterval);
            });
         }

         function ProcessData(data){
            if($scope.devices.length == 0)
                 $scope.devices = data.data;

             if($scope.devices.length == 0)
                SetTestData();
            else
            {
                for(var i = 0; i < $scope.devices.length; i++){
                    for(var j = 0; j < $scope.devices[i].lights.length; j++){
                        console.log(data);
                        $scope.devices[i].lights[j].state = data.data[i].lights[j].state;
                        $scope.devices[i].lights[j].dimmer = data.data[i].lights[j].dimmer;
                        $scope.devices[i].lights[j].color_temp = data.data[i].lights[j].color_temp;
                        $scope.devices[i].lights[j].hex_color = data.data[i].lights[j].hex_color;
                    }
                }
            }

             for (var i = 0; i < $scope.devices.length; i++){
                $scope.devices[i].lights[0].hex_color = "#" + $scope.devices[i].lights[0].hex_color;
                $scope.devices[i].name = getName($scope.devices[i]);
            }
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
                },
                {
                    index: 2,
                    application_type: 2,
                    last_seen: 1538726737,
                    reachable: true,
                    lights: [
                        {
                            supports_dimmer: true,
                            supports_temp: false,
                            supports_color: false,
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

         $scope.switchGroup = function(group, state)
         {
             if(state)
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

        $scope.changeColor = function(group){
              $http.post("/lighting/color_light?index="+group.index+"&color=" + group.lights[0].hex_color.substring(1));
        }

        function getName(group){
            var savedName = MemoryFactory.GetValue("Lighting"+group.index);
            if (!savedName)
                return group.index;
            return savedName;
        }

        $scope.startEdit = function(index){
            $scope.editing = index;
        }

        $scope.endEdit = function(index, name){
            if(!name)
                name = index;

            MemoryFactory.SetValue("Lighting" + index, name);
            $scope.editing = -1;
        }

         Init();
    });
})();