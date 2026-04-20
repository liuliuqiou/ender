const WebSocket = require("ws");
const http = require("http");
const { parseVLESSHeader } = require("./vless");

const UUID = "YOUR-UUID-HERE"; // ← 换成你的 UUID

const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end("Back4App VLESS Node Running");
});

const wss = new WebSocket.Server({ noServer: true });

server.on("upgrade", (req, socket, head) => {
    if (req.url !== "/ws") {
        socket.destroy();
        return;
    }
    wss.handleUpgrade(req, socket, head, (ws) => {
        wss.emit("connection", ws, req);
    });
});

wss.on("connection", (ws) => {
    ws.on("message", (msg) => {
        const header = parseVLESSHeader(msg);

        if (header.uuid.replace(/-/g, "") !== UUID.replace(/-/g, "")) {
            ws.close();
            return;
        }

        // 简化：直接回显（可改成转发）
        ws.send(Buffer.from("VLESS OK"));
    });
});

server.listen(3000, () => {
    console.log("VLESS server running on port 3000");
});
