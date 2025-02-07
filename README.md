# CSV URL Scraper

This project allows users to upload a CSV file containing URLs, scrape the metadata (title, description, keywords), and store it in a PostgreSQL database.

## Installation

1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd csv_url_scraper_project
   ```

2. Start the project using Docker:
   ```sh
   docker-compose up --build
   ```

## API Endpoints

- `POST /upload` - Upload a CSV file.
- `GET /status/{task_id}` - Check scraping progress.
- `GET /results/{id}` - Retrieve extracted metadata.

## Deployment

You can deploy the project on Railway, Render, or Fly.io.

## Monitoring

This project can be monitored using Prometheus and Grafana.
