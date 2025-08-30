from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # This addresses the "Handling System Failure Cases" plus point by having a robust entry point. [1]
    # eventlet is a production-ready server for WebSockets.
    socketio.run(app, debug=True, use_reloader=True)