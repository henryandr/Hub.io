var Device = {

  devices:[],

  load:function(){
    View.render('device/device','#right_view',{},function(){
      // Device.devices = [];
      if(Device.devices.length > 0)
        Device.load_devices();
      else
        Device.load_no_devices();
    });
  },

  load_devices:function(){
    View.render('device/device_wrapper','#device_container',{devices:Device.devices},function(){
      Device.devices = []; // Clean
    });
  },

  load_no_devices:function(){
    View.render('device/no_devices','#device_container',{},function(){});
  },

  pair_device:function(addr){
    toastr.info('Emparejando equipos...',"HUB.io");
    App.req_pair_device(addr);
  },

  set_devices:function(device){
    Device.devices.push(device);
    Device.load();
  }

}

var test_devices = [
  {'name':'UT-BLE201','addr':'01:05:06:19:5b'},
  {'name':'UT-BLE201','addr':'02:05:06:19:5b'}
]