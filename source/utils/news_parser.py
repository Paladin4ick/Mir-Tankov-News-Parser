import re

from bs4 import BeautifulSoup, Tag

from aiohttp import ClientSession, ClientError, ClientConnectionError, ClientTimeout, ClientResponseError

from loguru import logger

from source.config import ConfigBot

config = ConfigBot()


class NewsParser:
    def __init__(self):
        """
        Initializes the NewsParser with a base URL and an optional last published news link.

        Attributes:
            base_url (str): The base URL from which to fetch news articles.
            last_published_news_link (str or None): URL of the last published news article (if any).
        """
        self.base_url = "https://tanki.su/ru/news/"
        self.last_published_news_link = None

    @staticmethod
    async def get_html(session: ClientSession, url: str):
        try:
            async with session.get(url) as response:
                return await response.text()
        except (ClientError, ClientConnectionError, ClientTimeout, ClientResponseError) as e:
            logger.error(f"CLIENT_ERROR: {e}")

    @staticmethod
    async def get_news_image_url(news_item: Tag) -> str:
        """
         Extracts the image URL from a news item.

         This method looks for an element with the class '.preview_image-holder' within the
         provided news item. It extracts the URL of the image from the 'style' attribute
         of that element, processes it to ensure it is a complete URL, and returns it.

         Args:
             news_item (Tag): A BeautifulSoup Tag object representing a news item.

         Returns:
             str: The URL of the image. If no image URL is found, return "".
        """
        try:
            image_holder = news_item.select_one('.preview_image-holder')
            image_url = ""

            if image_holder:
                # Extract the value of the 'style' attribute.
                style_attr = image_holder.get('style', '')

                # Extract the image URL from the 'style' attribute string.
                start = style_attr.find('url(') + len('url(')
                end = style_attr.find(')', start)
                image_url = style_attr[start:end].strip('"').strip("'")

                # Add 'http:' to the URL if it starts with '//'.
                if image_url.startswith("//"):
                    image_url = "http:" + image_url

            return image_url
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(e)
            return ""

    async def get_latest_news(self, session: ClientSession) -> dict:
        """
        Retrieves the latest news article from the base URL.

        This asynchronous method fetches the HTML content from the base URL, parses it to
        find the latest news item, extracts relevant information such as the title,
        link to the news article, and image URL, and returns this information in a dictionary.

        Args:
            session (ClientSession): An aiohttp ClientSession object used to make the HTTP request.

        Returns:
            dict: A dictionary containing the title, link, and image URL of the latest news article.
        """
        try:
            # Fetch the HTML content using the aiohttp session.
            html = await self.get_html(session, self.base_url)

            # Create a BeautifulSoup object for parsing the HTML content.
            soup = BeautifulSoup(html, 'html.parser')

            # Get the HTML code for the most recently published news item.
            news_item = soup.select_one(".preview_item")

            # Get the title of the news article.
            title = news_item.select_one('.preview_title').get_text(strip=True)

            # Get the link to the news article.
            link = "https://tanki.su" + news_item.select_one('.preview_link')["href"]

            # Get the URL of the image associated with the news article.
            image_url = await self.get_news_image_url(news_item)

            # Return the news information as a dictionary.
            return {'title': title, 'link': link, 'image': image_url}
        except (AttributeError, TypeError, ValueError) as e:
            logger.error(e)
            return {'title': "None", 'link': "None", 'image': "None"}

    async def get_news_content(self, session: ClientSession, news_link: str) -> str:
        """
        Fetches and processes the content of a news article from the given link.

        This method retrieves the HTML content from the news article link, extracts text
        from all paragraph elements, replaces links with placeholders, and trims the
        content to ensure it doesn't end with a placeholder.

        Args:
            session (ClientSession): An aiohttp ClientSession object for making the HTTP request.
            news_link (str): The URL of the news article to fetch and process.

        Returns:
            str: The processed and trimmed text content of the news article.
        """
        try:
            # Fetch HTML content from the news link.
            html = await self.get_html(session, news_link)
            soup = BeautifulSoup(html, 'html.parser')

            # Extract all paragraph elements.
            paragraphs = soup.find_all('p')

            text_parts = []
            link_replacements = {}
            replacement_idx = 0

            # Process each paragraph to extract text and replace links.
            for p in paragraphs:
                text = p.get_text(strip=True)
                for a in p.find_all('a', href=True):
                    link_text = a.get_text(strip=True)
                    token = f"__LINK{replacement_idx}__"
                    text = text.replace(link_text, token)
                    link_replacements[token] = a['href']
                    replacement_idx += 1
                text_parts.append(text)

            full_text = "\n".join(text_parts)[:config.TEXT_LENGTH]

            # Remove any trailing placeholders
            trimmed_text = re.sub(r"__LINK\d+__$", "", full_text)

            # Replace placeholders with actual links
            for token, link in link_replacements.items():
                trimmed_text = trimmed_text.replace(token, link)

            return trimmed_text

        except (AttributeError, TypeError, ValueError) as e:
            logger.error(e)
            return ""

