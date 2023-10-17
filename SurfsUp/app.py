# Import the dependencies.

import numpy as np
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, join
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model

Base = automap_base()

# reflect the tables

Base.prepare(engine, reflect=True)

# Save references to each table

Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB

session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to the APP API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the precipitation data for the last year."""
    
    last_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = (func.datetime(last_date) - func.timedelta(days=365)).label("one_year_ago")

    results = (
        session.query(Measurement.date, Measurement.prcp, Station.name)
        .join(Station, Measurement.station == Station.station)
        .filter(Measurement.date >= one_year_ago)
        .all()
    )

    precipitation_dict = {
        date: {"prcp": prcp, "station_name": station_name}
    for date, prcp, station_name in results
    }

    return jsonify(precipitation_dict)


def stations():
    """Return a JSON list of stations from the dataset."""
    
    results_stations = session.query(Station.station, Station.name).all()

    stations_list = [{"station": station, "name": name} for station, name in results_stations]

    return jsonify(stations_list)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return the temperature observations for the most-active station for the last 12 months."""
    
    most_active_station = (
        session.query(Measurement.station, func.count(Measurement.station))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .first()
    )
    
    most_active_station_id = most_active_station[0]
    
    last_date_most_active = (
        session.query(func.max(Measurement.date))
        .filter(Measurement.station == most_active_station_id)
        .scalar()
    )
    
    one_year_ago_most_active = (func.datetime(last_date_most_active) - func.timedelta(days=365)).label("one_year_ago")

    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in results_most_active]

    return jsonify(tobs_list)


@app.route("/api/v1.0/<start>/<end>")
def temperature_start_end(start, end):
    """Return TMIN, TAVG, and TMAX for all dates greater than or equal to the start date."""
    
    results_start_end = (
        session.query(
            func.min(Measurement.tobs).label("TMIN"),
            func.avg(Measurement.tobs).label("TAVG"),
            func.max(Measurement.tobs).label("TMAX")
        )
        .filter(Measurement.date >= start)
        .filter(Measurement.date <= end)
        .all()
    )
    
    temperature_start_end_list = [
        {"TMIN": result[0], "TAVG": result[1], "TMAX": result[2]}
        for result in results_start_end
    ]

    return jsonify(temperature_start_end_list)

