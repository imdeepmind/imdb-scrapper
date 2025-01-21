import logging
import requests

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def make_get_request(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors

        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception("Failed to connect with IMDB server")
    except Exception as e:
        raise Exception("Something went wrong the server!!!")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def handle_scraping_errors(func):
    """Decorator to handle common scraping errors."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AttributeError as e:
            logger.error(f"Failed to find element: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to convert value: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    return wrapper


@dataclass
class MovieDetails:
    """Structure for movie details."""

    title: str
    release_year: Optional[str]
    rating: Optional[float]
    plot: str
    director: List[str]
    writer: List[str]
    stars: List[str]


@dataclass
class ScraperConfig:
    """Configuration settings for the IMDb scraper."""

    base_url: str = "https://www.imdb.com"
    search_path: str = "/search/title/"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
    selectors: Dict[str, str] = None

    def __post_init__(self):
        self.selectors = {
            "load_more": ".ipc-see-more__button",
            "movie_list": "ul.ipc-metadata-list",
            "movie_link": "a.ipc-title-link-wrapper",
            "title": "span[data-testid='hero__primary-text']",
            "plot": "p[data-testid='plot'] span",
            "credits": "li[data-testid='title-pc-principal-credit']",
            "rating": "div[data-testid='hero-rating-bar__aggregate-rating__score'] span",
            "release_date": "h1[data-testid='hero__pageTitle']",
        }


class IMDbMovieDetailsScraper:
    """Scraper for retrieving detailed information about a specific movie."""

    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()

    @handle_scraping_errors
    def __get_movie_title(self, soup: BeautifulSoup) -> str:
        """Extract movie title from the page."""
        title_elem = soup.select_one(self.config.selectors["title"])
        return title_elem.text if title_elem else ""

    @handle_scraping_errors
    def __get_movie_description(self, soup: BeautifulSoup) -> str:
        """Extract movie plot/description."""
        plot_elem = soup.select_one(self.config.selectors["plot"])
        return plot_elem.text if plot_elem else ""

    @handle_scraping_errors
    def __get_movie_credits(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract movie credits (director, writers, stars)."""
        credits = {"Director": [], "Writers": [], "Stars": []}
        credit_sections = soup.select(self.config.selectors["credits"])

        for section in credit_sections:
            title_elem = section.select_one("span") or section.select_one(
                "a.ipc-metadata-list-item__label"
            )
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            if title not in credits:
                continue

            names_list = section.select_one("ul.ipc-inline-list")
            if names_list:
                credits[title] = [
                    a.get_text(strip=True) for a in names_list.select("a")
                ]

        return credits

    @handle_scraping_errors
    def __get_release_date(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract movie release year."""
        title_elem = soup.select_one(self.config.selectors["release_date"])
        if not title_elem:
            return None

        release_elem = title_elem.find_parent("div").select_one("ul li a")
        return (release_elem.get_text(strip=True)) if release_elem else None

    @handle_scraping_errors
    def __get_movie_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract movie rating."""
        rating_elem = soup.select_one(self.config.selectors["rating"])
        return float(rating_elem.get_text(strip=True)) if rating_elem else None

    def get_movie_details(self, url: str) -> Optional[MovieDetails]:
        """
        Retrieve detailed information about a movie from its IMDb page.

        Args:
            url: Full URL of the movie's IMDb page.

        Returns:
            MovieDetails object containing the scraped information or None if failed.
        """
        try:
            content = self._make_request(url)
            if not content:
                return None

            soup = BeautifulSoup(content, "html.parser")
            credits = self.__get_movie_credits(soup)

            return MovieDetails(
                title=self.__get_movie_title(soup),
                release_year=self.__get_release_date(soup),
                rating=self.__get_movie_rating(soup),
                plot=self.__get_movie_description(soup),
                director=credits["Director"],
                writer=credits["Writers"],
                stars=credits["Stars"],
            )

        except Exception as e:
            logger.error(f"Failed to get movie details for {url}: {e}")
            return None

    def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP GET request with error handling."""
        try:
            return make_get_request(url)
        except Exception as e:
            logger.error(f"Failed to make request to {url}: {e}")
            return None


class IMDbMovieListScraper:
    """Scraper for retrieving lists of movies from IMDb search results."""

    def __init__(self, config: ScraperConfig = None):
        self.config = config or ScraperConfig()

    def __build_search_url(self, query: str) -> str:
        """Construct the search URL with the given query."""
        encoded_query = quote(query)
        return urljoin(
            self.config.base_url, f"{self.config.search_path}?title={encoded_query}"
        )

    def __setup_browser(self, playwright):
        """Set up and configure the browser instance."""
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            extra_http_headers={"User-Agent": self.config.user_agent}
        )
        page = context.new_page()
        return browser, page

    def __load_more_pages(self, page, max_pages: int) -> None:
        """Click 'Load more' button until max_pages is reached or no more content."""
        for page_num in range(max_pages):
            try:
                page.wait_for_selector(self.config.selectors["load_more"], timeout=5000)
                page.click(self.config.selectors["load_more"])
                logger.info(f"Loaded page {page_num + 2}")
            except PlaywrightTimeoutError:
                logger.info("No more content to load")
                break
            except Exception as e:
                logger.error(f"Error loading more content: {e}")
                break

    def __extract_movie_links(self, html_content: str) -> List[str]:
        """Extract movie links from the page content."""
        soup = BeautifulSoup(html_content, "html.parser")
        movie_links = []

        for ul in soup.select(self.config.selectors["movie_list"]):
            for link in ul.select(self.config.selectors["movie_link"]):
                if href := link.get("href"):
                    full_url = urljoin(self.config.base_url, href)
                    movie_links.append(full_url)

        return movie_links

    def get_movie_links(self, query: str, max_pages: int = 1) -> Optional[List[str]]:
        """
        Retrieve movie links from IMDb search results.

        Args:
            query: Movie title to search for.
            max_pages: Maximum number of pages to load (default: 1).

        Returns:
            List of movie URLs or None if an error occurs.
        """
        if not query.strip():
            raise ValueError("Search query cannot be empty")
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")

        try:
            with sync_playwright() as p:
                browser, page = self.__setup_browser(p)

                try:
                    search_url = self.__build_search_url(query)
                    page.goto(search_url)

                    if max_pages > 1:
                        self.__load_more_pages(page, max_pages - 1)

                    content = page.content()
                    movie_links = self.__extract_movie_links(content)

                    logger.info(f"Found {len(movie_links)} movie links")
                    return movie_links

                finally:
                    browser.close()

        except Exception as e:
            logger.error(f"Failed to get movie links: {e}")
            return None


class IMDbScraper:
    """Main class that combines movie list and detail scraping functionality."""

    def __init__(self, config: ScraperConfig = None, max_workers: int = 5):
        """
        Initialize the scraper.

        Args:
            config: Optional custom configuration settings
            max_workers: Maximum number of concurrent threads (default: 5)
        """
        self.config = config or ScraperConfig()
        self._list_scraper = IMDbMovieListScraper(self.config)
        self._details_scraper = IMDbMovieDetailsScraper(self.config)
        self._max_workers = max_workers

    def search_and_get_details(
        self,
        query: str,
        max_pages: int = 1,
    ) -> List[MovieDetails]:
        """
        Search for movies and get detailed information for each result using multiple threads.

        Args:
            query: Movie title to search for
            max_pages: Maximum number of pages to load (default: 1)

        Returns:
            List of MovieDetails objects
        """
        movie_links = self._list_scraper.get_movie_links(query, max_pages)

        if not movie_links:
            logger.warning("No movie links found")
            return []

        movie_details = []
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            # Submit all tasks
            futures = [
                executor.submit(self._details_scraper.get_movie_details, url)
                for url in movie_links
            ]

            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    details = future.result()
                    if details:
                        logger.info(f"Successfully scraped movie details")
                        movie_details.append(details)
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Failed to get movie details: {e}")
                    failed += 1

        logger.info(f"Completed scraping: {successful} successful, {failed} failed")
        return movie_details
