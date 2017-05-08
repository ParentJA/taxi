(function (window, angular, undefined) {

  'use strict';

  function DashboardController(AccountModel, Trip) {
    var vm = this;

    vm.models = {
      user: AccountModel.getUser()
    };

    vm.getCurrentTrips = function getCurrentTrips() {
      var trips = Trip.getCurrentTrips();
      if (vm.isRider()) {
        return _.filter(trips, function (trip) {
          return _.find(trip.rider, {id: vm.models.user.id});
        });
      }
      if (vm.isDriver()) {
        return _.filter(trips, function (trip) {
          return trip.driver !== null && trip.driver.id === vm.models.user.id;
        });
      }
    };

    vm.getTripsByStatus = function getTripsByStatus(status) {
      return Trip.getTripsByStatus(status);
    };

    vm.getCreated = function getCreated(trip) {
      return Trip.getCreated(trip);
    };

    vm.getTripsByFilter = function getTripsByFilter(filter) {
      return Trip.getTripsByFilter(filter);
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