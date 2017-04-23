(function (window, angular, undefined) {

  'use strict';

  function TripRouterConfig($stateProvider) {
    $stateProvider
      .state('app.trips', {
        url: '/trips',
        template: '<div ui-view></div>',
        data: {
          loginRequired: true
        },
        abstract: true
      })
      .state('app.trips.request', {
        url: '/request',
        templateUrl: 'trips/request.html',
        data: {
          loginRequired: false
        },
        controller: 'RequestController',
        controllerAs: 'vm'
      })
      .state('app.trips.detail', {
        url: '/:tripNk',
        templateUrl: 'trips/trip-detail.html',
        data: {
          loginRequired: false
        },
        resolve: {
          trip: function ($stateParams, Trip, TripResource) {
            var tripNk = $stateParams.tripNk;
            var trip = Trip.getTripByNk(tripNk);
            if (trip) {
              return trip;
            }
            else {
              return TripResource.retrieve(tripNk);
            }
          }
        },
        controller: 'TripDetailController',
        controllerAs: 'vm'
      });
  }

  angular.module('taxi')
    .config(['$stateProvider', TripRouterConfig]);

})(window, window.angular);