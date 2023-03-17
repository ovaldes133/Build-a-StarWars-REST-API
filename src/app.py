"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, People, Planet, user_favorite_planets, user_favorite_characters
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

"""@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200"""

@app.route('/people', methods=['GET'])
def get_all_people():
    people = People.query.all()
    if (people == []):
        return "people not found", 404
    else:
        people = list(map(lambda x: x.serialize(),people))
        return jsonify(people), 200

@app.route('/get_people/<int:people_id>', methods=['GET'])
def get_people(people_id):
    people = People.query.get(people_id)
    if people is None:
        return "people not found", 404   
    return people.serialize(), 200

@app.route('/planet', methods=['GET'])
def get_all_planet():
    planet = Planet.query.all()
    if (planet == []):
        return "planet not found", 404
    else:
        planet = list(map(lambda x: x.serialize(),planet))
        return jsonify(planet), 200

@app.route('/get_planet/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return "planet not found", 404   
    return planet.serialize(), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    if (users == []):
        return "users not found", 404
    else:
        users = list(map(lambda x: x.serialize(),users))
        return jsonify(users), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user = User.query.filter_by(is_active=True).first()
    if not user:
        return jsonify({'message': 'Active user not found'}), 404
    
    favorite_planets = []
    favorite_characters = []
    
    if user.favorite_planets:
        favorite_planets = Planet.query.join(user_favorite_planets).filter(user_favorite_planets.c.user_id == user.id).all()
    if user.favorite_characters:
        favorite_characters = People.query.join(user_favorite_characters).filter(user_favorite_characters.c.user_id == user.id).all()
        
    
    return jsonify({
        'favorite_planets': [planet.serialize() for planet in favorite_planets],
        'favorite_characters': [character.serialize() for character in favorite_characters]
    }), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = User.query.filter_by(is_active=True).first()
    if not user:
        return jsonify({'message': 'No active user found'}), 400

    planet = Planet.query.filter_by(id=planet_id).first()
    if not planet:
        return jsonify({'message': 'planet not found'}), 404

    if planet in user.favorite_planets:
        return jsonify({'message': 'planet already in favorites'}), 400

    user.favorite_planets.append(planet)
    db.session.commit()

    return jsonify({'message': 'planet added to favorites successfully'}), 200

@app.route('/favorite/character/<int:character_id>', methods=['POST'])
def add_favorite_character(character_id):
    user = User.query.filter_by(is_active=True).first()
    if not user:
        return jsonify({'message': 'No active user found'}), 400

    character = People.query.filter_by(id=character_id).first()
    if not character:
        return jsonify({'message': 'Character not found'}), 404

    if character in user.favorite_characters:
        return jsonify({'message': 'Character already in favorites'}), 400

    user.favorite_characters.append(character)
    db.session.commit()

    return jsonify({'message': 'Character added to favorites successfully'}), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"msg": "Planet not found"}), 404
    
    users = User.query.filter_by(is_active=True).filter(User.favorite_planets.any(id=planet_id)).all()

    for user in users:
        user.favorite_planets.remove(planet)
        db.session.commit()

    return jsonify({"msg": f"Planet {planet_id} was deleted"}), 200

@app.route('/favorite/people/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(character_id):
    character = People.query.get(character_id)
    if not character:
        return jsonify({"msg": "Character not found"}), 404
    
    users = User.query.filter_by(is_active=True).filter(User.favorite_characters.any(id=character_id)).all()

    for user in users:
        user.favorite_characters.remove(character)
        db.session.commit()

    return jsonify({"msg": f"Character {character_id} was deleted"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)