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
from models import db, User, Character, Planet, Favorite
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

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200


@app.route('/character', methods=['GET'])
def get_all_characters():

    characters = Character.query.all()
    all_characters = list(map(lambda x: x.serialize(), characters))

    return jsonify(all_characters), 200

@app.route('/character/<int:character_id>', methods=['GET'])
def get_character(character_id):

    character = Character.query.get(character_id)
    if character is None:
        return "No character with id " + str(character_id), 404
    one_character = character.serialize()

    return jsonify(one_character), 200

@app.route('/character', methods=['POST'])
def create_character():
    # Extract character data from the request JSON
    request_data = request.json
    name = request_data.get('name')
    birth_year = request_data.get('birth_year')
    gender = request_data.get('gender')

    if not name or not birth_year or not gender:
        return jsonify({"message": "Missing required fields"}), 400

    new_character = Character(name=name, birth_year=birth_year, gender=gender)

    db.session.add(new_character)
    db.session.commit()

    return jsonify(new_character.serialize()), 201

@app.route('/character/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):

    character_to_delete = Character.query.get(character_id)
    if character_to_delete is None:
        return "No character with id " + str(character_id), 404
    
    db.session.delete(character_to_delete)
    db.session.commit()

    return "Character with id " + str(character_id) + " has been deleted", 200 

@app.route('/character/<int:character_id>', methods=['PUT'])
def update_character(character_id):
    updated_character = request.get_json()
    old_character = Character.query.get(character_id)

    if old_character is None:
        return "No character with id " + str(character_id), 404

    if 'name' in updated_character:
        old_character.name = updated_character['name']
    if 'birth_year' in updated_character:
        old_character.birth_year = updated_character['birth_year']
    if 'gender' in updated_character:
        old_character.gender = updated_character['gender']

    db.session.commit()

    return "Character with id " + str(character_id) + " has been updated", 200


@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    all_planets = list(map(lambda x: x.serialize(), planets))
    return jsonify(all_planets), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"message": f"No planet with id {planet_id}"}), 404
    return jsonify(planet.serialize()), 200


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    all_users = list(map(lambda x: x.serialize(), users))
    return jsonify(all_users), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({"message": "Missing User-ID header"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    all_favorites = list(map(lambda x: x.serialize(), favorites))
    return jsonify(all_favorites), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({"message": "Missing User-ID header"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"message": "Planet not found"}), 404
    
    favorite = Favorite(user_id=user.id, planet_id=planet.id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify(favorite.serialize()), 201

@app.route('/favorite/character/<int:character_id>', methods=['POST'])
def add_favorite_character(character_id):
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({"message": "Missing User-ID header"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    character = Character.query.get(character_id)
    if not character:
        return jsonify({"message": "Character not found"}), 404
    
    favorite = Favorite(user_id=user.id, character_id=character.id)
    db.session.add(favorite)
    db.session.commit()

    return jsonify(favorite.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({"message": "Missing User-ID header"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    favorite = Favorite.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404
    
    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite deleted"}), 200

@app.route('/favorite/character/<int:character_id>', methods=['DELETE'])
def delete_favorite_character(character_id):
    user_id = request.headers.get('User-ID')
    if not user_id:
        return jsonify({"message": "Missing User-ID header"}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    favorite = Favorite.query.filter_by(user_id=user.id, character_id=character_id).first()
    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404
    
    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorite deleted"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)