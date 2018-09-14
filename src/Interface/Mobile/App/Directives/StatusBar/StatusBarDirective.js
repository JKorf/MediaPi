(function () {
    angular.module('pi-test').directive('statusBar', function ($rootScope, $state, RequestFactory) {
        return {
            restrict: 'E',
            scope: {
            },
            templateUrl: '/App/Directives/StatusBar/statusbar.html',
            link: function ($scope, element, attrs) {
                statusInterval = RequestFactory.StartRequesting("/util/status", 2000, handleStatus, handleError);

                var normal = "#999";
                var orange = "#e07700";
                var yellow = "#f7ff21";
                var green = "#7bff0f";
                var red = "#ff2b2b";

                function handleStatus(response){
                    $scope.data = response.data;
                    $(".status-ellipse").css('background', colorForTorrentState($scope.data.torrent_state, $scope.data.buffer_ready, $scope.data.peers_connected, $scope.data.potential_peers));

                    var memcolor = colorForMemory($scope.data.memory);
                    if (memcolor == normal)
                        $(".memory-item").css('color', "");
                    else
                        $(".memory-item").css('color', memcolor);

                    var cpucolor = colorForCpu($scope.data.cpu);
                    if (cpucolor == normal)
                        $(".cpu-item").css('color', "");
                    else
                        $(".cpu-item").css('color', cpucolor);
                }

                function handleError(err){
                    console.log(err);
                    $scope.data = null;
                }

                function colorForTorrentState(torrent_state, bytes_ready, connected_peers, potential_peers){

                    if (torrent_state == 2 && connected_peers == 0 && potential_peers == 0) // Downloading metadata but no available peers
                        return orange;

                    if (torrent_state == 3 && connected_peers == 0 && potential_peers == 0) // Downloading and no available peers
                        return orange;

                    if (torrent_state == 3 && bytes_ready < 4500000) // Downloading and less than 4.5mb in buffer
                        return yellow;

                    return green;
                }

                function colorForMemory(mem){
                    if (mem < 80)
                        return normal;
                    if (mem < 94)
                        return orange;
                    return red;
                }

                function colorForCpu(cpu){
                    if (cpu < 40)
                        return normal;
                    if (cpu < 60)
                        return orange;
                    return red;
                }
            }
        };
    });
})();