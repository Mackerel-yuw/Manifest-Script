新建 ping-pong

写入 ping-pong/server.py
"""
#!/usr/bin/env python3
import http.server, socketserver, os, webbrowser, threading
os.chdir(os.path.dirname(__file__))
PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler
def open_browser():
    webbrowser.open(f"http://localhost:{PORT}")
threading.Timer(1.0, open_browser).start()
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Ping-Pong running at http://localhost:{}".format(PORT))
    httpd.serve_forever()
"""

写入 ping-pong/index.html
"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <title>Ping-Pong</title>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{margin:0;background:#003366;display:flex;justify-content:center;align-items:center;height:100vh}
    canvas{background:#003366;border:2px solid #fff}
  </style>
</head>
<body>
  <canvas id="c" width="800" height="400"></canvas>
  <script src="game.js"></script>
</body>
</html>
"""

写入 ping-pong/game.js
"""
const cvs = document.getElementById('c');
const ctx = cvs.getContext('2d');
const W = cvs.width, H = cvs.height;

let ball   = { x: W/2, y: H/2, vx: 4, vy: 3, r: 10 };
let paddleL = H/2, paddleR = H/2, speed = 6;

function rect(x,y,w,h){ ctx.fillRect(x,y,w,h); }

function loop(){
    ctx.fillStyle = '#003366';
    ctx.fillRect(0,0,W,H);

    ball.x += ball.vx;
    ball.y += ball.vy;

    if(ball.y - ball.r < 0 || ball.y + ball.r > H) ball.vy *= -1;

    if(ball.x - ball.r < 30 && ball.y > paddleL-50 && ball.y < paddleL+50) ball.vx =  Math.abs(ball.vx);
    if(ball.x + ball.r > W-30 && ball.y > paddleR-50 && ball.y < paddleR+50) ball.vx = -Math.abs(ball.vx);

    if(ball.x < 0 || ball.x > W){ ball.x = W/2; ball.y = H/2; }

    window.onkeydown = e => {
        switch(e.key.toLowerCase()){
            case 'a': paddleL = Math.max(50, paddleL-speed); break;
            case 'z': paddleL = Math.min(H-50, paddleL+speed); break;
            case 'k': paddleR = Math.max(50, paddleR-speed); break;
            case 'm': paddleR = Math.min(H-50, paddleR+speed); break;
        }
    };

    ctx.fillStyle = '#ffff00';
    rect(ball.x-ball.r, ball.y-ball.r, ball.r*2, ball.r*2);
    rect(10, paddleL-50, 10, 100);
    rect(W-20, paddleR-50, 10, 100);

    requestAnimationFrame(loop);
}

window.onload = loop;
"""

运行 python ping-pong/server.py