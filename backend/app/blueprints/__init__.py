from app.blueprints.games_bp import games_bp
from app.blueprints.teams_bp import teams_bp
from app.blueprints.players_bp import players_bp


def init_blueprints(app):
    with app.app_context():
        app.register_blueprint(games_bp, url_prefix="/games")
        app.register_blueprint(teams_bp, url_prefix="/teams")
        app.register_blueprint(players_bp, url_prefix="/players")
