var Patient = {

  load:function(){
    View.render('patient/patient','#right_view',{},function(){
      Patient.init();
      $('#patient_save').on('click',Patient.save_info);
    });
  },

  init:function(){
    App.socket.emit('read_info',{});

    keyboard_config = {
      language:'es',
      layout: 'international',
      position: {of:'body',my:'center top'}
    };

    $('#given_name').keyboard(keyboard_config)
    $('#surname').keyboard(keyboard_config)
  },

  save_info:function(){
    given_name = $('#given_name').val();
    surname = $('#surname').val();

    if(given_name && surname){
      App.socket.emit('save_info',{given_name:given_name,surname:surname});
      toastr.success('Información guardada correctamente.',"HUB.io");
    }else
      toastr.error('Complete todos los campos, por favor.',"HUB.io");
  },

  read_info:function(msg){
    $('#given_name').val(msg.given_name);
    $('#surname').val(msg.surname);
  }
}