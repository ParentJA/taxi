(function (window, angular, undefined) {

  'use strict';

  function HttpConfig($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
  }

  function CoreRouterConfig($stateProvider, $urlRouterProvider) {
    $stateProvider
      .state('app', {
        url: '/app',
        template: '<div ui-view></div>',
        data: {
          loginRequired: true
        },
        abstract: true
      })
      .state('landing', {
        url: '/',
        templateUrl: 'global/landing.html',
        data: {
          loginRequired: false
        },
        controller: 'LandingController',
        controllerAs: 'vm'
      });

    //Default state.
    $urlRouterProvider.otherwise('/');
  }

  function CoreRunner($rootScope, $state, AccountModel, navigationService) {
    $rootScope.$state = $state;
    $rootScope.$on('$stateChangeStart', function (event, toState) {
      // Close navigation.
      navigationService.closeNavigation();

      // Check authentication.
      if (toState.data.loginRequired && !AccountModel.hasUser()) {
        event.preventDefault();
        $state.go('log_in');
      }
    });
  }

  function MainController($state, $websocket, AccountModel, growl, logOutService, navigationService) {
    var vm = this;

    vm.navigationService = navigationService;

    vm.hasUser = function hasUser() {
      return AccountModel.hasUser();
    };

    vm.logOut = function logOut() {
      logOutService().finally(function () {
        $state.go('log_in');
      });
    };

    function onConnect(message) {
      console.log('Connected.');
    }

    function onReceive(message) {
      growl.info('Message received.');
    }

    function onDisconnect(message) {
      console.log('Disconnected.');
    }

    function init() {
      var dataStream = $websocket('ws://localhost:8000/');
      dataStream.onOpen(onConnect);
      dataStream.onMessage(onReceive);
      dataStream.onOpen(onDisconnect);
    }

    init();
  }

  angular.module('templates', []);

  angular.module('taxi', ['angular-growl', 'angular-websocket', 'templates', 'ui.bootstrap', 'ui.router', 'ngAnimate'])
    .constant('BASE_URL', '/api/')
    .config(['$httpProvider', HttpConfig])
    .config(['$stateProvider', '$urlRouterProvider', CoreRouterConfig])
    .config(['growlProvider', function(growlProvider) {
      growlProvider.globalTimeToLive(2000);
    }])
    .run(['$rootScope', '$state', 'AccountModel', 'navigationService', CoreRunner])
    .controller('MainController', [
      '$state', '$websocket', 'AccountModel', 'growl', 'logOutService', 'navigationService', MainController
    ]);

})(window, window.angular);