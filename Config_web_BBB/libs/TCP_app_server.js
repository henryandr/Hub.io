const net = require('net');

const HOST = '127.0.0.1';
const PORT = 9000;

net.createServer(function(sock) {
  global.sock = sock;

  console.log('CONNECTED: ' + sock.remoteAddress +':'+ sock.remotePort);

  sock.on('data', function(data) {
    data = JSON.parse(data);
    switch(data.type){
      case 'new_device':
        send_to_ws.connection_request(data);
        break;
      case 'paired':
        send_to_ws.paired_device(data);
        break;
      case 'data':
        send_to_ws.measurement_data(data);
        break;
    }
  });

  sock.on('close', function(data) {
    console.log('CLOSED: ' + sock.remoteAddress +' '+ sock.remotePort);
  });

  sock.on("error",function(e){
    console.error("Error: " + e.stack);
  });
    
}).listen(PORT, HOST);

console.log('Server listening on ' + HOST +':'+ PORT);