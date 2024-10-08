# FlaskFusion

## Project Overview

FlaskFusion is an advanced software application designed for data analysis and manipulation, focused on containerization and deployment technologies. The application handles various data types including tabular data, RGB images, and textual data, providing users with a seamless experience for uploading, processing, and visualizing their data.

## Features

- **Tabular Data Handling:** Upload, process, and perform CRUD operations on CSV files. Compute advanced statistics and generate dynamic visualizations.
- **RGB Image Processing:** Upload and manipulate images, generate color histograms, and perform batch processing.
- **Textual Data Analysis:** Perform text summarization, keyword extraction, and sentiment analysis.
- **Rich Front-End:** An engaging user interface built with React, utilizing animations and responsive design.

## Technologies Used

- **Backend:** Python, Flask
- **Database:** MongoDB
- **Containerization:** Docker
- **Frontend:** React, Tailwind CSS

## Installation

### Prerequisites

- Python 3.x
- MongoDB version 7.0 or higher running

### Setup

#### Running with Bash Script

To run the application in development mode, run the following command:

```bash
bash start_dev.sh
```

To run the application in production mode, run the following command:

```bash
bash start_prod.sh
```

#### Running with Docker

```bash
docker build -t flaskfusion .
docker run -p 5000:5000 flaskfusion
```

#### Running with Docker Compose

```bash
docker-compose up -d
```

## Usage

- Navigate to http://localhost:5000

## License

This project is licensed under the MIT License.
