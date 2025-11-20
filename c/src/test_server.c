/**
 * test_server.c - Simple HTTP Test Server Implementation
 */

#include "test_server.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <time.h>
#include <stdbool.h>

/* Server state */
static int server_fd = -1;
static uint16_t server_port = TEST_SERVER_PORT;
static bool server_running = false;

/* Test HTML page */
static const char *test_page_html =
    "<!DOCTYPE html>\n"
    "<html>\n"
    "<head>\n"
    "    <title>PQ-Tor Test Server</title>\n"
    "    <style>\n"
    "        body { font-family: Arial, sans-serif; margin: 50px; background: #f0f0f0; }\n"
    "        .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }\n"
    "        h1 { color: #333; }\n"
    "        .success { color: #28a745; font-size: 24px; font-weight: bold; }\n"
    "        .info { color: #666; margin-top: 20px; }\n"
    "    </style>\n"
    "</head>\n"
    "<body>\n"
    "    <div class=\"container\">\n"
    "        <h1>PQ-Tor Test Server</h1>\n"
    "        <p class=\"success\">✓ Anonymous connection successful!</p>\n"
    "        <div class=\"info\">\n"
    "            <p>You have successfully accessed this test server through the PQ-Tor network.</p>\n"
    "            <p>Your connection was anonymized using:</p>\n"
    "            <ul>\n"
    "                <li>Post-Quantum Ntor Handshake (Kyber KEM)</li>\n"
    "                <li>3-hop Circuit (Guard → Middle → Exit)</li>\n"
    "                <li>AES-256-CTR Onion Encryption</li>\n"
    "            </ul>\n"
    "            <p><strong>Timestamp:</strong> %s</p>\n"
    "        </div>\n"
    "    </div>\n"
    "</body>\n"
    "</html>\n";

/**
 * Initialize test server
 */
int test_server_init(uint16_t port) {
    server_port = port;

    // Create socket
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        perror("socket");
        return -1;
    }

    // Set socket options
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt");
        close(server_fd);
        return -1;
    }

    // Bind to port
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(server_port);

    if (bind(server_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        close(server_fd);
        return -1;
    }

    // Listen
    if (listen(server_fd, TEST_SERVER_MAX_CLIENTS) < 0) {
        perror("listen");
        close(server_fd);
        return -1;
    }

    printf("[TestServer] Server initialized on port %u\n", server_port);
    return 0;
}

/**
 * Handle HTTP request
 */
static void handle_http_request(int client_fd, const char *client_ip) {
    char buffer[TEST_SERVER_BUFFER_SIZE];
    char response[TEST_SERVER_BUFFER_SIZE];
    char html[TEST_SERVER_BUFFER_SIZE];

    // Read request
    ssize_t n = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
    if (n <= 0) {
        return;
    }
    buffer[n] = '\0';

    // Parse request line
    char method[16], path[256], version[16];
    if (sscanf(buffer, "%15s %255s %15s", method, path, version) != 3) {
        const char *bad_request = "HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n";
        send(client_fd, bad_request, strlen(bad_request), 0);
        return;
    }

    printf("[TestServer] %s %s from %s\n", method, path, client_ip);

    // Only support GET
    if (strcmp(method, "GET") != 0) {
        const char *method_not_allowed = "HTTP/1.1 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n";
        send(client_fd, method_not_allowed, strlen(method_not_allowed), 0);
        return;
    }

    // Get current timestamp
    time_t now = time(NULL);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S UTC", gmtime(&now));

    // Generate HTML with timestamp
    int html_len = snprintf(html, sizeof(html), test_page_html, timestamp);

    // Send HTTP response
    int header_len = snprintf(response, sizeof(response),
                             "HTTP/1.1 200 OK\r\n"
                             "Content-Type: text/html; charset=utf-8\r\n"
                             "Content-Length: %d\r\n"
                             "Connection: close\r\n"
                             "\r\n",
                             html_len);

    send(client_fd, response, header_len, 0);
    send(client_fd, html, html_len, 0);
}

/**
 * Start test server (blocking)
 */
int test_server_run(void) {
    if (server_fd < 0) {
        fprintf(stderr, "[TestServer] Server not initialized\n");
        return -1;
    }

    server_running = true;
    printf("[TestServer] Server running on port %u\n", server_port);
    printf("[TestServer] Access at: http://localhost:%u/\n", server_port);

    while (server_running) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);

        int client_fd = accept(server_fd, (struct sockaddr*)&client_addr, &client_len);
        if (client_fd < 0) {
            if (errno == EINTR) continue;
            perror("accept");
            break;
        }

        char *client_ip = inet_ntoa(client_addr.sin_addr);
        printf("[TestServer] Connection from %s:%d\n",
               client_ip, ntohs(client_addr.sin_port));

        handle_http_request(client_fd, client_ip);
        close(client_fd);
    }

    return 0;
}

/**
 * Stop test server
 */
void test_server_stop(void) {
    server_running = false;
    if (server_fd >= 0) {
        close(server_fd);
        server_fd = -1;
    }
    printf("[TestServer] Server stopped\n");
}
