(function () {

    angular.module('pi-test').config(function($stateProvider, $urlRouterProvider) {


        $stateProvider.state('home', {
            url: '/',
            templateUrl: '/App/Modules/Home/home.html',
            cache: false,
            controller: "HomeController"
        });

        $stateProvider.state('lighting', {
            url: '/lighting',
            templateUrl: '/App/Modules/Lighting/lighting.html',
            cache: false,
            controller: "LightingController"
        });

        $stateProvider.state('tv', {
            url: '/tv',
            templateUrl: '/App/Modules/TV/tv.html',
            cache: false,
            controller: "TVController"
        });

        $stateProvider.state('movies', {
            url: '/media/movies',
            templateUrl: '/App/Modules/Media/medialist.html',
            cache: false,
            controller: "MediaListController"
        });

        $stateProvider.state('movie', {
            url: '/movie/:id',
            templateUrl: '/App/Modules/Movies/movie.html',
            cache: false,
            controller: "MovieController"
        });

        $stateProvider.state('shows', {
            url: '/media/shows',
            templateUrl: '/App/Modules/Media/medialist.html',
            cache: false,
            controller: "MediaListController"
        });

        $stateProvider.state('show', {
            url: '/show/:id',
            templateUrl: '/App/Modules/Shows/show.html',
            cache: false,
            controller: "ShowController"
        });

        $stateProvider.state('torrents', {
            url: '/torrents',
            templateUrl: '/App/Modules/Torrents/torrents.html',
            cache: false,
            controller: "TorrentsController"
        });

        $stateProvider.state('hd', {
            url: '/hd/:path',
            templateUrl: '/App/Modules/HD/hd.html',
            cache: false,
            controller: "HDController"
        });

        $stateProvider.state('radio', {
            url: '/radio',
            templateUrl: '/App/Modules/Radio/radio.html',
            cache: false,
            controller: "RadioController"
        });

        $stateProvider.state('youtube', {
            url: '/media/youtube',
            templateUrl: '/App/Modules/Media/medialist.html',
            cache: false,
            controller: "MediaListController"
        });

        $stateProvider.state('youtube-channel', {
            url: '/youtube/:id',
            templateUrl: '/App/Modules/YouTube/youtube.html',
            cache: false,
            controller: "YouTubeChannelController"
        });

        $stateProvider.state('statistics', {
            url: '/statistics',
            templateUrl: '/App/Modules/Statistics/statistics.html',
            cache: false,
            controller: "StatisticsController"
        });

        $stateProvider.state('settings', {
            url: '/settings',
            templateUrl: '/App/Modules/Settings/settings.html',
            cache: false,
            controller: "SettingsController"
        });

        $stateProvider.state('history', {
            url: '/history',
            templateUrl: '/App/Modules/History/history.html',
            cache: false,
            controller: "HistoryController"
        });

        $urlRouterProvider.otherwise('/');
    });
})();