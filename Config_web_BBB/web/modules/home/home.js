var Home = {

	load:function(){
		View.render('home/home','#app_container',{},function(){
			Include.myModule('device',function(){
        Device.load();
      });
    });
    setTimeout(Home.init_home,200);
	},

  init_home:function(){
    $('#search').on('click',Home.load_device);
    $('#measure').on('click',Home.load_measure);
    $('#patient').on('click',Home.load_patient);
  },

  load_device:function(){
    Device.load();
  },

  load_measure:function(){
    if(typeof Measure === 'undefined')
      Include.myModule('measure',function(){
        Measure.load();
      });
    else
      Measure.load();
  },

  load_patient:function(){
    if(typeof Patient === 'undefined')
      Include.myModule('patient',function(){
        Patient.load();
      });
    else
      Patient.load();
  }
  
}
