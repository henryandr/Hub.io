var Measure = {

  measures:[],

  load:function(){
    View.render('measure/measure','#right_view',{},function(){
      // Measure.measures = test_measures; // Test
      if(Measure.measures.length > 0)
        Measure.load_measures();
      else
        Measure.load_no_measures();
    });
  },

  load_measures:function(){
    View.render('measure/measure_wrapper','#measure_container',{measures:Measure.measures},function(){
      Measure.measures = []; // Clean
    });
  },

  load_no_measures:function(){
    View.render('measure/no_measures','#measure_container',{},function(){});
  },

  set_measure:function(measure){
    toastr.success('Medidas enviadas',"HUB.io");
    measure = Measure.filter_measures(measure.data);
    console.log(measure);
    Measure.measures = measure;
    Measure.load();
  },

  filter_measures:function(measures){
    m = [];
    for (var i = 0; i < measures.length; i++) {
      switch(measures[i].name){
        case 'Temperature Measurement':
          measures[i].name = 'Temperatura';
          measures[i].units = '°' + measures[i].units;
          m.push(measures[i]);
          break;
        case 'Blood Pressure Measurement':
          switch(measures[i].var){
            case 'Pulse Rate':
              measures[i].name = 'Pulso cardiaco';
              measures[i].units = measures[i].units;
              m.push(measures[i]);
              break;
            case 'Systolic':
              measures[i].name = 'Presión sistólica';
              measures[i].units = measures[i].units;
              m.push(measures[i]);
              break;
            case 'Diastolic':
              measures[i].name = 'Presión diastólica';
              measures[i].units = measures[i].units;
              m.push(measures[i]);
              break;
            case 'Mean Pressure':
              measures[i].name = 'Presión media';
              measures[i].units = measures[i].units;
              m.push(measures[i]);
              break;
          }
      }
    }
    return m;
  }
}