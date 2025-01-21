# IMDb Web Scraper

This repository contains the solution for the assignment "IMDb Web Scraper," which involves building a Python Django application to scrape movie data from IMDb. The application allows searching for movies by a specific genre or keyword, handles pagination, and stores the extracted data in a structured format. It also provides RESTful APIs to interact with the data.



## Approach

1. **Handling Pagination**:  
   - IMDb is a Single Page Application (SPA) that uses JavaScript to load data dynamically. For pagination, the website uses a "Load More" button that triggers AJAX calls to fetch additional results.
   - To handle this, I use **Playwright** as it provides a headless browser capable of executing JavaScript. Playwright allows me to:
     - Load the page.
     - Click the "Load More" button multiple times based on a specified parameter.
     - Extract the updated HTML of the page after all results are loaded.

2. **Extracting Movie Links**:  
   - Once the HTML is extracted, it is passed to **BeautifulSoup** for parsing.
   - BeautifulSoup is used to extract the links to individual movie pages from the loaded results.

3. **Fetching Movie Details**:  
   - For each extracted movie link, an HTTP request is fired to load the individual movie page.
   - Since IMDb uses Server-Side Rendering (SSR) for individual movie pages, there is no need to use a headless browser here.
   - The HTML of the page is loaded into BeautifulSoup, and the required information (title, release year, rating, plot, etc.) is extracted.

4. **Storing the Data**:  
   - Once the data is extracted, it is stored in a structured format using **Django ORM**.



## Features

- **Scraped Data**: Collects and stores the following details for each movie:
  - `title: str`
  - `release_year: Optional[str]`
  - `rating: Optional[float]`
  - `plot: str`
  - `director: List[str]`
  - `writer: List[str]`
  - `stars: List[str]`
- **Supports 3 APIs**:
  - **Scrape API**: Trigger IMDb scraping for a specified genre or keyword.
  - **Get All Movies API**: Retrieve all scraped movies with pagination support.
  - **Search API**: Perform searches based on specific parameters like title or genre.
- **Handles Pagination**: Automatically navigates through multiple pages of search results using Playwright.
- **Multithreading Support**: Improves scraping performance for large datasets.
- **Error Handling**: Ensures smoother operation by handling errors gracefully.



## Installation and Setup

### Prerequisites

Ensure Docker is installed on your system.

### Steps to Run the Project

1. **Build the Docker Image**:
   ```bash
   docker build -t imdb_scrapper .
   ```

2. **Run the Application**:
   ```bash
   docker run -p 8000:8000 imdb_scrapper
   ```

3. Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000).



## How to Use

1. **Run the Scraper**:  
   Use the Scrape API to fetch data from IMDb by specifying a genre or keyword.  
   Example:
   ```
   POST /api/movies/scrap/?query=<query>&max_pages=<max_page>
   ```

2. **Get All Movies**:  
   Retrieve all scraped movies using the pagination-supported API.  
   Example:
   ```
   GET /api/movies/?page=1&page_size=10
   ```

3. **Search Movies**:  
   Perform a search for movies by title or other attributes. This API also supports pagination.  
   Example:
   ```
   GET /api/movies/search?title=Dark&person=Nolan&min_rating=9&title=Dark
   ```



## Limitations

- **SQLite Database**: The project uses SQLite, which is suitable for small-scale applications but not ideal for production-grade systems.
- **Scraping on API Call**: Scraping is triggered directly via the Scrape API, which may cause timeout issues for large datasets. A queue service like RabbitMQ or Celery would be better for handling this asynchronously, but it is beyond the scope of this assignment.



## Notes

- **Unit Tests**: Unit tests are not included due to time constraints. However, the APIs have been manually tested for functionality.
- **Future Improvements**: Migrating to a more robust database and implementing asynchronous scraping would enhance scalability and reliability.
- **Timeout Issue**: When scrapping, keep the `max_pages` very small. Otherwise scrapping process might take long time and cause a timeout issue.
- **sqlite**: I have added one sqlite file in the repo with several scrapped movies so testing the APIs can easily be done.

