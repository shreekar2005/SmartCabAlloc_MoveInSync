from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # for WebSockets.
    socketio.run(app, debug=True, use_reloader=True)