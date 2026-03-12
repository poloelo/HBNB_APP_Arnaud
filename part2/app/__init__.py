from flask import Flask
from flask_restx import Api

def create_app():
    from app.services import facade
    facade.reset()

    app = Flask(__name__)
    api = Api(
        app,
        version='1.0',
        title='HBnB API',
        description='HBnB Application API',
        doc='/api/v1/'
    )

    from app.api.v1.users import api as users_ns
    api.add_namespace(users_ns, path='/api/v1/users')

    from app.api.v1.places import api as places_ns
    api.add_namespace(places_ns,    path='/api/v1/places')

    from app.api.v1.amenities import api as amenities_ns
    api.add_namespace(amenities_ns, path='/api/v1/amenities')

    from app.api.v1.reviews import api as reviews_ns
    api.add_namespace(reviews_ns,   path='/api/v1/reviews')

    from app.api.v1.bookings import api as bookings_ns
    api.add_namespace(bookings_ns,  path='/api/v1/bookings')


    return app
