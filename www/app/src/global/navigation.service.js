(function (window, angular, undefined) {

  'use strict';

  function navigationService() {
    var navigationOpen = false;

    this.closeNavigation = function closeNavigation() {
      navigationOpen = false;
    };

    this.isNavigationOpen = function isNavigationOpen() {
      return navigationOpen;
    };

    this.openNavigation = function openNavigation() {
      navigationOpen = true;
    };

    this.toggleNavigation = function toggleNavigation() {
      navigationOpen = !navigationOpen;
    };
  }

  angular.module('taxi')
    .service('navigationService', [navigationService]);

})(window, window.angular);