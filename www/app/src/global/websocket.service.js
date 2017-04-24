(function (window, angular, undefined) {

  'use strict';

  function websocketService($websocket, AccountModel, Trip, TripStatus, growl) {
    var websocket = {};

    this.connect = function connect() {
      var url = AccountModel.isRider() ? 'ws://localhost:8000/rider/' : 'ws://localhost:8000/driver/';
      websocket = $websocket(url);
      websocket.onOpen(onConnect);
      websocket.onMessage(onReceive);
      websocket.onClose(onDisconnect);
    };

    this.send = function send(data) {
      return websocket.send(data);
    };

    this.disconnect = function disconnect() {

    };

    function onConnect(message) {
      console.log('Connected.');
    }

    function onReceive(message) {
      var data = JSON.parse(message.data);
      if (AccountModel.isRider()) {
        var status = data.status;
        switch (status) {
          case TripStatus.STARTED:
            growl.info('Your driver is headed to the pick up address.');
            break;
          case TripStatus.IN_PROGRESS:
            growl.info('Your driver is headed to the drop off address.');
            break;
          case TripStatus.COMPLETED:
            growl.info('You have arrived.');
            break;
        }
      }
      else {
        if (data.status === TripStatus.REQUESTED) {
          growl.info('Someone needs a ride.');
        }
      }
      Trip.updateDict(data);
    }

    function onDisconnect(message) {
      console.log('Disconnected.');
    }
  }

  angular.module('taxi')
    .service('websocketService', ['$websocket', 'AccountModel', 'Trip', 'TripStatus', 'growl', websocketService]);

})(window, window.angular);