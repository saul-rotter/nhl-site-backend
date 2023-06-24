from app import create_app
from app.blueprints.init_ns import api

if __name__ == '__main__':
    app = create_app()
    api.init_app(app)
    app.run(debug=True)
else:
    app = create_app()
