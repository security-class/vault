import os

from app import app, server

debug = (os.getenv('DEBUG', 'False') == 'True')
port = os.getenv('PORT', '5000')

if __name__ == "__main__":
    print "Vault Service Starting..."
    server.initialize_redis()
    app.run(host='0.0.0.0', port=int(port), debug=debug)
