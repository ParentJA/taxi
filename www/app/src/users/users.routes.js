(function (window, angular, undefined) {

  'use strict';

  function AuthorizationRouterConfig($stateProvider) {
    // Account-based config.
    $stateProvider
      .state('log_in', {
        url: '/log_in',
        templateUrl: 'users/log-in.html',
        data: {
          loginRequired: false
        },
        controller: 'LogInController',
        controllerAs: 'vm'
      })
      .state('sign_up', {
        url: '/sign_up',
        templateUrl: 'users/sign-up.html',
        data: {
          loginRequired: false
        },
        controller: 'SignUpController',
        controllerAs: 'vm'
      });
  }

  angular.module('taxi')
    .config(['$stateProvider', AuthorizationRouterConfig]);

})(window, window.angular);