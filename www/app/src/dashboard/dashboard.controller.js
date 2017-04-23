(function (window, angular, undefined) {

  'use strict';

  function DashboardController(AccountModel, Trip) {
    var vm = this;

    vm.models = {
      user: AccountModel.getUser()
    };

    vm.getCurrentTrips = function getCurrentTrips() {
      return Trip.getCurrentTrips();
    };

    vm.getTripsByStatus = function getTripsByStatus(status) {
      return Trip.getTripsByStatus(status);
    };

    vm.getCreated = function getCreated(trip) {
      return Trip.getCreated(trip);
    };

    vm.isRider = function isRider() {
      return AccountModel.isRider();
    };

    vm.isDriver = function isDriver() {
      return AccountModel.isDriver();
    };
  }

  angular.module('taxi')
    .controller('DashboardController', ['AccountModel', 'Trip', DashboardController]);

})(window, window.angular);