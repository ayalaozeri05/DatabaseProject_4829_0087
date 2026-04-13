CREATE TABLE VEHICLE
(
  plate_number VARCHAR(15) NOT NULL,
  vehicle_type VARCHAR(50) NOT NULL,
  capacity INT NOT NULL CHECK (capacity > 0),
  PRIMARY KEY (plate_number)
);

CREATE TABLE REGION
(
  region_id INT NOT NULL,
  regio_name VARCHAR(50) NOT NULL,
  terrain_type VARCHAR(50) NOT NULL,
  description VARCHAR(255),
  PRIMARY KEY (region_id)
);

CREATE TABLE ROUTE
(
  route_id INT NOT NULL,
  route_name VARCHAR(100) NOT NULL,
  start_location VARCHAR(100) NOT NULL,
  end_location VARCHAR(100) NOT NULL,
  estimated_duration_minutes INT NOT NULL CHECK (estimated_duration_minutes > 0),
  total_distance_km FLOAT NOT NULL CHECK (total_distance_km >= 0),
  created_date DATE NOT NULL,
  region_id INT NOT NULL,
  PRIMARY KEY (route_id),
  FOREIGN KEY (region_id) REFERENCES REGION(region_id)
);

CREATE TABLE SITE
(
  site_name VARCHAR(100) NOT NULL,
  site_type VARCHAR(50) NOT NULL,
  address VARCHAR(255),
  PRIMARY KEY (site_name)
);

CREATE TABLE STOP
(
  stop_id INT NOT NULL,
  stop_name VARCHAR(100) NOT NULL,
  address VARCHAR(255) NOT NULL,
  latitude FLOAT NOT NULL CHECK (latitude BETWEEN -90 AND 90),
  longitude FLOAT NOT NULL CHECK (longitude BETWEEN -180 AND 180),
  site_name VARCHAR(100) NOT NULL,
  PRIMARY KEY (stop_id),
  FOREIGN KEY (site_name) REFERENCES SITE(site_name)
);

CREATE TABLE TRIP
(
  trip_id INT NOT NULL,
  trip_date DATE NOT NULL,
  departure_time VARCHAR(5) NOT NULL,
  available_seats INT NOT NULL CHECK (available_seats >= 0),
  route_id INT NOT NULL,
  plate_number VARCHAR(15) NOT NULL,
  PRIMARY KEY (trip_id),
  FOREIGN KEY (route_id) REFERENCES ROUTE(route_id),
  FOREIGN KEY (plate_number) REFERENCES VEHICLE(plate_number)
);

CREATE TABLE ROUTE_STOP
(
  stop_order INT NOT NULL CHECK (stop_order > 0),
  estimated_arrival_time VARCHAR(5) NOT NULL,
  route_id INT NOT NULL,
  stop_id INT NOT NULL,
  PRIMARY KEY (route_id, stop_id),
  FOREIGN KEY (route_id) REFERENCES ROUTE(route_id),
  FOREIGN KEY (stop_id) REFERENCES STOP(stop_id),
  UNIQUE (route_id, stop_order)
);

CREATE TABLE REGION_VEHICLE
(
  region_id INT NOT NULL,
  plate_number VARCHAR(15) NOT NULL,
  PRIMARY KEY (region_id, plate_number),
  FOREIGN KEY (region_id) REFERENCES REGION(region_id),
  FOREIGN KEY (plate_number) REFERENCES VEHICLE(plate_number)
);