const http = require('http');

let tasks = [];
let idCounter = 1;

const server = http.createServer((req, res) => {
  const isTasksPath = req.url === '/tasks' || req.url === '/api/tasks';

  if (isTasksPath && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(tasks));
  } else if (isTasksPath && req.method === 'POST') {
    let body = '';
    let bodyLength = 0;
    const MAX_SIZE = 1048576; // 1MB
    
    req.on('data', chunk => {
      bodyLength += chunk.length;
      if (bodyLength > MAX_SIZE) {
        if (!res.headersSent) {
          res.writeHead(413, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Payload Too Large' }));
        }
        req.destroy();
      } else {
        body += chunk.toString();
      }
    });
    
    req.on('end', () => {
      if (bodyLength > MAX_SIZE) return;
      try {
        const data = JSON.parse(body);
        if (!data.title) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Title is required' }));
          return;
        }
        const newTask = { id: idCounter++, title: data.title };
        tasks.push(newTask);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(newTask));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
      }
    });
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
});

const PORT = 3000;
if (require.main === module) {
  server.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
  });
}

module.exports = server;
