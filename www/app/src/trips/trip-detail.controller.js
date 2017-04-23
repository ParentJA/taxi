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
      var trip = _.merge(vm.models.trip, data);
      TripResource.update(trip).then(function () {}, function () {});
    };
  }

  angular.module('taxi')
    .controller('TripDetailController', [
      'AccountModel', 'Trip', 'TripResource', 'TripStatus', 'trip', TripDetailController]);

})(window, window.angular);