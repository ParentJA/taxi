(function (window, angular, undefined) {

  'use strict';

  function TripDetailController(AccountModel, Trip, TripResource, TripStatus, trip) {
    var vm = this;

    vm.models = {
      trip: trip
    };

    vm.isRider = function isRider() {
      return AccountModel.isRider();
    };

    vm.isDriver = function isDriver() {
      return AccountModel.isDriver();
    };

    vm.getCreated = function getCreated(trip) {
      return Trip.getCreated(trip);
    };

    vm.updateTripStatus = function updateTripStatus(status) {
      var data = {status: status};
      if (status === TripStatus.STARTED) {
        data['driver'] = AccountModel.getUser();
      }
      TripResource.update(trip.nk, data).then(function () {
        vm.models.trip = Trip.getTripByNk(vm.models.trip.nk);
      }, function () {});
    };
  }

  angular.module('taxi')
    .controller('TripDetailController', [
      'AccountModel', 'Trip', 'TripResource', 'TripStatus', 'trip', TripDetailController]);

})(window, window.angular);