const http = require('http');
const fs = require('fs');
const path = require('path');

const filePath = path.resolve(__dirname, '..', 'data_douyin', '奥创毁灭地球.html');

const server = http.createServer((req, res) => {
  fs.readFile(filePath, 'utf-8', (err, data) => {
    if (err) {
      res.writeHead(500);
      res.end('Error loading file');
      return;
    }
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(data);
  });
});

server.listen(19876, '0.0.0.0', () => {
  console.log('Serving at:');
  console.log('  http://localhost:19876');
  console.log('  http://127.0.0.1:19876');
  // Get LAN IP
  const os = require('os');
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) {
        console.log(`  http://${net.address}:19876`);
      }
    }
  }
});
