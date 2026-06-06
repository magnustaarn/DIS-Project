# How to compile

## Prerequisites

Python 3.11 or newer

PostgreSQL 16

pip

## Install Dependencies

Clone the repository and install the required Python packages:
```bash
git clone <repository-url>
cd wikipedia-speedrun
pip install -r requirements.txt
```
## Database Setup

Create a PostgreSQL database:
```sql
CREATE DATABASE wikipedia_speedrun;
```
Connect to the database and execute the schema script:
```bash
psql -U postgres -d wikipedia_speedrun -f Wikispeedrun.sql
```
## Configure Database Credentials

Set the database password as an environment variable:

Linux/macOS:
```bash
export DB_PASSWORD=your_password
```
Windows:
```CMD
set DB_PASSWORD=your_password
```
Update the database name in DB_CONFIG if necessary.

## Initialize the Graph

Insert at least one starting page into the pages table:
```sql
INSERT INTO pages(title) VALUES ('Copenhagen');
```
Run the crawler:
```bash
python db_populate.py
```
The crawler will download Wikipedia pages, extract internal links using regular expressions, and populate the pages and links_to tables.

## Running the Web Application

Start the web application:
```bash
python app.py
```
The application will be available at:

http://127.0.0.1:5000 (flask default)

(Replace the command and port if the final web application uses a different framework.)
