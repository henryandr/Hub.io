const socketio = require('socket.io');
var fs = require('fs');

global.io = socketio.listen(server);

io.sockets.on('connection', function (socket) {

  console.log('Client connected');

  socket.on('conn_rsp', send_to_ws.connection_response);
  socket.on('save_info', send_to_ws.save_info);
  socket.on('read_info', send_to_ws.read_info);

  socket.on('disconnect', function(){
    console.log('Client disconnected');
  });

});

global.send_to_ws = {

  connection_request:function(msg){
    io.sockets.emit('new_device', msg);
  },

  connection_response:function(msg){
    console.log(msg);
    sock.write(msg);
  },

  paired_device:function(msg){
    io.sockets.emit('paired', msg);
  },

  measurement_data:function(msg){
    io.sockets.emit('new_measure', msg);
    console.log(msg);
  },

  save_info:function(msg){
    fs.writeFile("./patient.json", JSON.stringify(msg), function(err) {
      if(err) {
          console.log(err);
      }

      console.log('The file was saved!');
    }); 
  },

  read_info:function(){
    fs.readFile('./patient.json', {encoding: 'utf-8'}, function(err,data){
      if (!err)
        io.sockets.emit('read_info', JSON.parse(data));
      else 
        console.log(err);
    });
  }
}