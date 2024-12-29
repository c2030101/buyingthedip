from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import os


def run_server(port=8000):
    """Run a simple HTTP server to view the trade report"""
    # Change to the output directory
    os.chdir('./output')

    # Start the server
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)

    # Open the trade report in the default browser
    webbrowser.open(f'http://localhost:{port}/trade_report.html')

    print(f"Server started at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()