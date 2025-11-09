This project provides a custom and postgresql Prometheus exporters collecting metrics for weather, air quality, Mars weather, and cryptocurrency prices, along with a PostgreSQL database. It can be run fully via Docker.

1. Clone the repository
git clone https://github.com/askhat00/ShopSphere-Analytics2.git
cd yourproject

2. Build and run Docker containers

The project uses Docker Compose to launch all services (Prometheus, Grafana, custom exporter, PostgreSQL).

docker-compose up -d --build


Prometheus: http://localhost:9090

Grafana: http://localhost:3000

Custom Exporter Metrics: http://localhost:8000/metrics

3. Running the Custom Exporter Locally

python custom_exporter.py


It will expose metrics on port 8000 by default.

4. Running db.py

This script interacts with the database and simulates active:

python db.py


Ensure your PostgreSQL database is running.

Update database credentials in db.py as needed.
