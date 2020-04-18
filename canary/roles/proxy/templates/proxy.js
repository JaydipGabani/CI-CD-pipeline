var http = require("http");
var httpProxy = require("http-proxy");
var request = require("request");
var exec = require("child_process").exec;
var fs = require("fs");

let count = 0;
let alert = false;

var proxy = httpProxy.createProxyServer({});

prod_url = fs.readFileSync("stableServer").toString();
canary_url = fs.readFileSync("canaryServer").toString();

console.log(prod_url);
console.log(canary_url);

/** The server running at 3000 port acts as a loadbalancer which sends 
75% of traffic to Stable server and 25% of traffice to canary server*/
http
  .createServer(function (req, res) {
    console.log("Canary server serving request!");
    console.log(req.url);
    //proxy.web(req, res, { target: "http://192.168.33.30:3000/" });
    proxy.web(req, res, { target: "http://192.168.33.40:3000/" });
    console.log(res.statusCode);
    console.log(res);
  })
  .listen(3000);

/* Checks health of the canary server every 500ms and raises 'Alert' message
when it cannot reach canary server atleast 4 times */
// var heartbeatTimer = setInterval(function () {
//   var options = {
//     url: canary_url,
//   };

//   request(options, function (error, res, body) {
//     if (!error && res.statusCode == 200) {
//       count = 0;
//       alert = false;
//     } else {
//       if (count != Number.MAX_VALUE) count++;
//     }
//     if (count >= 4) {
//       console.log("Alert!!! Canary server is not reachable!");
//       alert = true;
//     }
//   });
// }, 500);