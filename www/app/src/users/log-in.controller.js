(function (window, angular, undefined) {

  'use strict';

  function LogInController($state, logInService, websocketService) {
    var vm = this;
    
    vm.error = {};
    vm.form = '';
    vm.password = null;
    vm.username = null;

    vm.hasError = function hasError() {
      return !_.isEmpty(vm.error);
    };

    vm.onSubmit = function onSubmit() {
      logInService(vm.username, vm.password).then(function () {
        websocketService.connect();
        $state.go('app.dashboard');
      }, function (response) {
        vm.error = response;
        vm.password = null;
      });
    };
  }

  angular.module('taxi')
    .controller('LogInController', ['$state', 'logInService', 'websocketService', LogInController]);

})(window, window.angular);