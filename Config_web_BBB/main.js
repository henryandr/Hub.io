

/* Web Server */
const express  = require('express');
const app = express();
global.server = require("http").Server(app);
const bodyParser = require('body-parser');

const port = 8081;
// const ip = "127.0.0.1"
const ip = "0.0.0.0"

app.use(express.static(__dirname + '/web')); // Root path to index.html

app.use(bodyParser.urlencoded({ extended: true })); // Allow urlencoded
app.use(bodyParser.json()); // Allow application/json MIME media type

/* WS Server Web communication */
require('./libs/WS_conn');

/* TCP Server Python communication */
require('./libs/TCP_app_server');

/* Start server */

server.listen(port,ip,function(){
    console.log('Express ready on port ' + port);
});