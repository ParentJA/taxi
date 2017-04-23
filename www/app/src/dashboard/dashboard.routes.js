(function (window, angular, undefined) {

  'use strict';

  function DashboardRouterConfig($stateProvider) {
    $stateProvider.state('app.dashboard', {
      url: '/dashboard',
      templateUrl: 'dashboard/dashboard.html',
      data: {
        loginRequired: true
      },
      resolve: {
        trips: function (TripResource) {
          return TripResource.list();
        }
      },
      controller: 'DashboardController',
      controllerAs: 'vm'
    });
  }

  angular.module('taxi')
    .config(['$stateProvider', DashboardRouterConfig]);

})(window, window.angular);