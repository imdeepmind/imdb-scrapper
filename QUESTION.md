Article type: Project
IMDb Web Scraper
Objective: Create a Python web scraper that extracts movie information from IMDb. The scraper should be able to handle pagination and extract specific details about movies from multiple pages.



Requirements:

Use IMDb's search functionality to search for a specific genre or keyword (e.g., "comedy" or "action"). Extract movie details from the search results.

Write a Python Django script that scrapes the following information for each movie:
Title
Release Year
IMDb Rating
Director(s)
Cast
Plot Summary
Handle pagination.
If the search results span multiple pages, make sure your scraper can navigate through them and extract data from all pages.


Leverage Django's ORM to store the extracted data in a structured format and use Django REST Framework to develop APIs for interacting with the scraped data
Provide clear instructions on how to run the scraper and any dependencies it might have.


Bonus Points:

Implement error handling and logging to handle unexpected issues gracefully.
Include unit tests to validate the functionality of your scraper.
Implement multiprocessing or asynchronous programming to improve scraping performance.
Allow the user to specify the genre or keyword for the search.


Submission Guidelines:

Submit the Python script along with any necessary configuration files.
Include a README file explaining how to run the scraper, install dependencies, and any additional information about the project.
If you've implemented bonus functionalities, explain them in the README.


Evaluation Criteria:

Code Quality: Evaluate the clarity, readability, and structure of the code. Look for proper naming conventions, comments, and consistent indentation.
Functionality: Check if the scraper successfully extracts movie information from multiple pages and handles pagination correctly. Ensure that the extracted data is accurate and complete.
Error Handling: Evaluate how the script handles errors and edge cases. Bonus points if the code includes meaningful error messages and logging.
Bonus Functionalities: If the candidate has implemented any bonus functionalities, assess the quality and effectiveness of those features.
Testing: If unit tests are provided, evaluate their coverage and effectiveness in validating the scraper's functionality.