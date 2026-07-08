package com.example.camlan;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.concurrent.atomic.AtomicReference;

import com.sun.net.httpserver.HttpServer;

public class App {
    private static final int PORT = 8080;
    private static final AtomicReference<Process> pythonProcess = new AtomicReference<>();

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress("0.0.0.0", PORT), 0);

        server.createContext("/", exchange -> {
            byte[] body = buildIndexHtml().getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "text/html; charset=UTF-8");
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        server.createContext("/start", exchange -> {
            byte[] body;
            if (pythonProcess.get() == null || !pythonProcess.get().isAlive()) {
                startPythonServer();
                body = "started".getBytes(StandardCharsets.UTF_8);
            } else {
                body = "already-running".getBytes(StandardCharsets.UTF_8);
            }
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        server.createContext("/stop", exchange -> {
            stopPythonServer();
            byte[] body = "stopped".getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        server.createContext("/info", exchange -> {
            String json = "{\"host\":\"" + getLocalIp() + "\",\"port\":" + PORT + "}";
            byte[] body = json.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });

        server.setExecutor(null);
        server.start();
        System.out.println("Java browser launcher started at http://" + getLocalIp() + ":" + PORT);
    }

    private static void startPythonServer() {
        try {
            Path projectDir = Paths.get("..").toAbsolutePath().normalize();
            Path venvPython = projectDir.resolve(".venv").resolve("Scripts").resolve("python.exe");
            Path fallbackPython = Paths.get("python");

            ProcessBuilder pb;
            if (Files.exists(venvPython)) {
                pb = new ProcessBuilder(venvPython.toString(), "server/cam_server_gui.py");
            } else {
                pb = new ProcessBuilder(fallbackPython.toString(), "server/cam_server_gui.py");
            }

            pb.directory(projectDir.toFile());
            pb.redirectErrorStream(true);
            Process process = pb.start();
            pythonProcess.set(process);
            Thread monitor = new Thread(() -> {
                try {
                    process.waitFor();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    pythonProcess.compareAndSet(process, null);
                }
            });
            monitor.setDaemon(true);
            monitor.start();
            System.out.println("Started Python server process");
        } catch (IOException e) {
            System.err.println("Failed to start Python server: " + e.getMessage());
        }
    }

    private static void stopPythonServer() {
        Process process = pythonProcess.get();
        if (process != null && process.isAlive()) {
            process.destroy();
            pythonProcess.set(null);
        }
    }

    private static String getLocalIp() {
        try {
            return InetAddress.getLocalHost().getHostAddress();
        } catch (Exception e) {
            return "127.0.0.1";
        }
    }

    private static String buildIndexHtml() {
        return """
            <!doctype html>
            <html lang=\"en\">
            <head>
                <meta charset=\"utf-8\">
                <title>Cam LAN Java Browser Launcher</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #111; color: #f5f5f5; margin: 0; padding: 24px; }
                    .panel { max-width: 980px; margin: 0 auto; }
                    button { padding: 8px 12px; margin-right: 8px; }
                    iframe { width: 100%; height: 720px; border: 2px solid #444; margin-top: 16px; background: #222; }
                </style>
            </head>
            <body>
                <div class=\"panel\">
                    <h2>Cam LAN Browser Launcher</h2>
                    <p>Start the Python camera server from here, then open the stream in your browser.</p>
                    <button onclick=\"startServer()\">Start server</button>
                    <button onclick=\"stopServer()\">Stop server</button>
                    <p id=\"status\">Status: idle</p>
                    <iframe id=\"viewer\" src=\"http://127.0.0.1:5000/\"></iframe>
                </div>
                <script>
                    async function startServer() {
                        const response = await fetch('/start', {method: 'POST'});
                        const text = await response.text();
                        document.getElementById('status').textContent = 'Status: ' + text;
                        setTimeout(() => window.location.reload(), 1000);
                    }
                    async function stopServer() {
                        const response = await fetch('/stop', {method: 'POST'});
                        const text = await response.text();
                        document.getElementById('status').textContent = 'Status: ' + text;
                    }
                </script>
            </body>
            </html>
            """;
    }
}
