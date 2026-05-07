var App = {

  socket:null,

	body_load:function(){
		Include.myModule('home',function(){
        Home.load();
    });
    toastr.options.closeButton = true;
    setTimeout(App.init_socket,1000);
	},

  init_socket:function(){
    // var socket = io.connect('http://localhost:8081');
    App.socket = io.connect('http://192.168.7.2:8081',{transports:['websocket']});

    App.socket.on('new_device',App.new_device);
    App.socket.on('paired',App.paired);
    App.socket.on('new_measure',App.new_measure);
    App.socket.on('read_info',App.read_info);
  },

  new_device:function(data){
    console.log(data);
    Device.set_devices(data);
  },

  paired:function(){
    toastr.remove();
    toastr.success('Dispositivo emparejado correctamente',"HUB.io");
    Device.load();
  },

  new_measure:function(data){
    console.log(data);
    if(typeof Measure === 'undefined')
      Include.myModule('measure',function(){
        Measure.set_measure(data);
      });
    else
      Measure.set_measure(data);
  },

  req_pair_device:function(addr){
    App.socket.emit('conn_rsp',addr);
  },

  read_info:function(msg){
    Patient.read_info(msg);
  }

}