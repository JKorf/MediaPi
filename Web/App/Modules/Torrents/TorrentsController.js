(function () {

    angular.module('pi-test').controller('TorrentsController', function ($scope, $interval, $http, $state, ConfirmationFactory, RequestFactory, CacheFactory) {
        $scope.torrentStates = [];
        $scope.torrentStates[0] = "-";
        $scope.torrentStates[1] = "Initial";
        $scope.torrentStates[2] = "Downloading Metadata";
        $scope.torrentStates[3] = "Downloading";
        $scope.torrentStates[4] = "Paused";
        $scope.torrentStates[5] = "Done";

        $scope.torrents = [];

        Init();

        $scope.removeTorrent = function(torrent){
            if(torrent.streaming){
                if(!confirm('Removing this torrent will stop the video player, do you want to continue?'))
                    return
            }
            else if (torrent.state != 5){
                if(!confirm('Removing this torrent will cancel the download, do you want to continue?'))
                    return;
            }

            $http.post("/torrents/remove?id="+torrent.id);
            $scope.torrents.splice($scope.torrents.indexOf(torrent), 1);
        }

        $scope.getText = function(torrent){
            if ($scope.torrentStates[torrent.state] != "Downloading")
                return $scope.torrentStates[torrent.state]
            else
                return torrent.speed+"/ps"
        }

        function Init(){
            var torrentInterval = RequestFactory.StartRequesting("/torrents/get", 2000, handleTorrentInfo, handleTorrentError)

            $scope.$on("$destroy", function(){
                RequestFactory.StopRequesting(torrentInterval);
            });
        }

        function handleTorrentInfo(response){
            if (response.data.length != $scope.torrents.length){
                $scope.torrents = response.data;
            }
            else
            {
                for(var i = 0 ; i < response.data.length; i++){
                    var t = $.grep($scope.torrents, function(e){ return e.id == response.data[i].id; });
                    if (t.length == 0){
                        $scope.torrents = response.data;
                        break;
                    }

                    t[0].connected_peers = response.data[i].connected_peers;
                    t[0].connecting_peers = response.data[i].connecting_peers;
                    t[0].downloaded = response.data[i].downloaded;
                    t[0].id = response.data[i].id;
                    t[0].left = response.data[i].left;
                    t[0].name = response.data[i].name;
                    t[0].percentage_done = response.data[i].percentage_done;
                    t[0].potential_peers = response.data[i].potential_peers;
                    t[0].size = response.data[i].size;
                    t[0].speed = response.data[i].speed;
                    t[0].state = response.data[i].state;
                    t[0].stream_buffer_ready = response.data[i].stream_buffer_ready;
                    t[0].stream_buffer_total = response.data[i].stream_buffer_total;
                    t[0].streamed = response.data[i].streamed;
                    t[0].streaming = response.data[i].streaming;
                }
            }
        }

        function handleTorrentError(err){
            console.log(err);
            $scope.torrents = [];
        }
    });
})()