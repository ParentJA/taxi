(function (window, angular, undefined) {

  'use strict';

  function RequestController($state, AccountModel, TripResource) {
    var vm = this;
    
    vm.error = {};
    vm.form = '';
    vm.pickUpAddress = null;
    vm.dropOffAddress = null;

    vm.hasError = function hasError() {
      return !_.isEmpty(vm.error);
    };

    vm.onSubmit = function onSubmit() {
      TripResource.create({
        drop_off_address: vm.dropOffAddress,
        pick_up_address: vm.pickUpAddress,
        riders: [AccountModel.getUser()]
      }).then(function () {
        $state.go('app.dashboard');
      }, function (response) {
        vm.error = response;
        vm.pickUpAddress = null;
        vm.dropOffAddress = null;
      });
    };
  }

  angular.module('taxi')
    .controller('RequestController', ['$state', 'AccountModel', 'TripResource', RequestController]);

})(window, window.angular);