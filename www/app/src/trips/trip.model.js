(function (window, angular, undefined) {

  'use strict';

  function Trip(TripStatus) {
    var trips = {};

    this.getTripByNk = function getTripByNk(nk) {
      return trips[nk];
    };

    this.getTripsByStatus = function getTripsByStatus(status) {
      return _.filter(trips, {status: status});
    };

    this.getCurrentTrips = function getCurrentTrips() {
      return _.reject(trips, {status: TripStatus.COMPLETED});
    };

    this.getTrips = function getTrips() {
      return trips;
    };

    this.removeDict = function removeDict(nk) {
      delete trips[nk];
    };

    this.updateDict = function updateDict(data) {
      if (!_.isUndefined(data)) {
        trips[data.nk] = data;
      }
    };

    this.updateList = function updateList(data) {
      if (!_.isUndefined(data)) {
        trips = _.merge(trips, _.keyBy(data, 'nk'));
      }
    };

    this.getCreated = function getCreated(trip) {
      return moment(trip.created).format('MMM D YYYY, h:mm:ss a');
    };
  }

  angular.module('taxi')
    .constant('TripStatus', {
      REQUESTED: 'REQUESTED',
      STARTED: 'STARTED',
      IN_PROGRESS: 'IN_PROGRESS',
      COMPLETED: 'COMPLETED'
    })
    .service('Trip', ['TripStatus', Trip]);

})(window, window.angular);