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
            $scope.devices= [
                        { id: 1,
                          name: "Woonkamer spots",
                          state: false,
                          warmth: 260,
                          dimmer: 200},
                          { id: 2,
                          name: "Woonkamer overige",
                          state: true,
                          warmth: 290,
                          dimmer: 100}
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
                $http.post("/lighting/switch_light?id="+group.id+"&state=on");
             else
                $http.post("/lighting/switch_light?id="+group.id+"&state=off");
         };

         $scope.dimmerGroup = function(group){
              $http.post("/lighting/dimmer_light?id="+group.id+"&dimmer=" + group.dimmer);
         }

         $scope.warmthGroup = function(group){
              $http.post("/lighting/warmth_light?id="+group.id+"&warmth=" + group.warmth);
         }

         Init();
    });
})();