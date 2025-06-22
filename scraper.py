import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import random
import re

class WebScraper:
    def __init__(self):
        """Initialize the WebScraper with Chrome webdriver."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            # Fallback to simple Chrome initialization
            self.driver = webdriver.Chrome(options=chrome_options)
    
    def scrape_news_content(self, url):
        """Scrape content from a news article URL."""
        try:
            # First try with requests + BeautifulSoup as it's faster
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for article content in common containers
                content = ""
                for selector in ['article', '.article-content', '.story-body', '.entry-content', 'main', '.content']:
                    elements = soup.select(selector)
                    if elements:
                        paragraphs = elements[0].find_all('p')
                        if paragraphs:
                            content = ' '.join([p.text for p in paragraphs])
                            break
                
                # If we found content, return it
                if content:
                    return content
            
            # If requests approach failed, try with Selenium
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Look for article content with Selenium
            for selector in ['article', '.article-content', '.story-body', '.entry-content', 'main', '.content']:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        paragraphs = elements[0].find_elements(By.TAG_NAME, 'p')
                        if paragraphs:
                            return ' '.join([p.text for p in paragraphs])
                except:
                    continue
            
            # Last resort: grab whatever text we can
            body = self.driver.find_element(By.TAG_NAME, 'body')
            paragraphs = body.find_elements(By.TAG_NAME, 'p')
            if paragraphs:
                return ' '.join([p.text for p in paragraphs[:10]])  # Limit to first 10 paragraphs
            else:
                return body.text[:3000]  # Get first 3000 chars of body
                
        except Exception as e:
            print(f"Error scraping content from {url}: {e}")
            return f"Could not extract content from this source. Error: {str(e)}"

    def scrape_direct_from_source(self, source_name):
        """Scrape news directly from specific news sources"""
        try:
            source_configs = {
                "times_of_india": {
                    "url": "https://timesofindia.indiatimes.com/india",
                    "article_selector": ".w_tle, .list5 li, .w_img_title",
                    "title_selector": "h3, a span, figcaption",
                    "link_selector": "a",
                    "base_url": "https://timesofindia.indiatimes.com"
                },
                "hindustan_times": {
                    "url": "https://www.hindustantimes.com/latest-news",
                    "article_selector": ".hdg3, .media, .storyCard, .cartHolder",
                    "title_selector": "h3, .hdg3-text, .media-heading",
                    "link_selector": "a",
                    "base_url": "https://www.hindustantimes.com"
                },
                "the_hindu": {
                    "url": "https://www.thehindu.com/latest-news/",
                    "article_selector": ".element, .story-card, .story-card-33, .ES2-100x4-text1",
                    "title_selector": "h3, .title, .card-title",
                    "link_selector": "a",
                    "base_url": "https://www.thehindu.com"
                },
                "ndtv": {
                    "url": "https://www.ndtv.com/india",
                    "article_selector": ".news_item, .lisingNews, .new_storylisting_img, .src_itm-ptb",
                    "title_selector": "h2, .newsHdng, .item-title",
                    "link_selector": "a",
                    "base_url": "https://www.ndtv.com"
                },
                "india_today": {
                    "url": "https://www.indiatoday.in/india",
                    "article_selector": ".detail, .B1S3_story__card, .catagory-listing, .view-content",
                    "title_selector": ".title, h3, .section_title",
                    "link_selector": "a",
                    "base_url": "https://www.indiatoday.in"
                }
            }
            
            source_config = source_configs.get(source_name)
            if not source_config:
                return []
                
            self.driver.get(source_config["url"])
            time.sleep(3)  # Wait for page to load
            
            # Find articles
            articles = self.driver.find_elements(By.CSS_SELECTOR, source_config["article_selector"])
            results = []
            
            # Process up to 5 articles
            for article in articles[:5]:
                try:
                    # Get title
                    title_elem = None
                    try:
                        title_elem = article.find_element(By.CSS_SELECTOR, source_config["title_selector"])
                    except:
                        continue
                        
                    title = title_elem.text.strip()
                    if not title:
                        continue
                    
                    # Get link
                    link_elem = article.find_element(By.CSS_SELECTOR, source_config["link_selector"])
                    link = link_elem.get_attribute('href')
                    
                    if not link:
                        continue
                        
                    # Make sure it's an absolute URL
                    if link.startswith('/'):
                        link = source_config["base_url"] + link
                    
                    # Get content
                    content = self.scrape_news_content(link)
                    
                    # Format source name for display
                    display_name = source_name.replace('_', ' ').title()
                    
                    results.append({
                        'title': title,
                        'link': link,
                        'source': display_name,
                        'time': f"Recent - {datetime.now().strftime('%B %d, %Y')}",
                        'content': content
                    })
                    
                except Exception as e:
                    print(f"Error scraping article from {source_name}: {e}")
                    continue
                    
            return results
            
        except Exception as e:
            print(f"Error scraping from {source_name}: {e}")
            return []

    def scrape_technical_source(self, source_name, query):
        """Scrape content from technical learning platforms"""
        try:
            # Technical sources configuration
            tech_source_configs = {
                "geeksforgeeks": {
                    "search_url": f"https://www.geeksforgeeks.org/search/?q={query.replace(' ', '+')}",
                    "result_selector": ".article-card, .gfg_home_page_article_card, .g-card, .gs-webResult",
                    "title_selector": "a.gs-title, .title, h2, .head",
                    "link_selector": "a.gs-title, .title a, h2 a, a.head",
                    "snippet_selector": ".gs-snippet, .content, .entry-content, .text",
                    "base_url": "https://www.geeksforgeeks.org"
                },
                "javatpoint": {
                    "search_url": f"https://www.javatpoint.com/search.php?search={query.replace(' ', '+')}",
                    "result_selector": "tr.mx-auto, .gsc-webResult, .gs-webResult",
                    "title_selector": "a.gsc-result-info-title, .gs-title, .link-title, h3",
                    "link_selector": "a.gsc-result-info-title, .gs-title, h3 a",
                    "snippet_selector": ".gs-snippet, .gsc-table-result, .overview",
                    "base_url": "https://www.javatpoint.com"
                },
                "tutorialspoint": {
                    "search_url": f"https://www.tutorialspoint.com/search.htm?search={query.replace(' ', '+')}",
                    "result_selector": ".gsc-webResult, .result-box, .search_result",
                    "title_selector": ".gs-title, .result-title, h3 a",
                    "link_selector": ".gs-title a, .result-title a",
                    "snippet_selector": ".gs-snippet, .result-text",
                    "base_url": "https://www.tutorialspoint.com"
                },
                "w3schools": {
                    "search_url": f"https://www.w3schools.com/search.php?q={query.replace(' ', '+')}",
                    "result_selector": ".search_item, .gs-webResult, .ws-table-all tr",
                    "title_selector": ".search_item_title, .gs-title, td a",
                    "link_selector": ".search_item_title a, .gs-title a",
                    "snippet_selector": ".search_item_text, .gs-snippet",
                    "base_url": "https://www.w3schools.com"
                },
                "stackoverflow": {
                    "search_url": f"https://stackoverflow.com/search?q={query.replace(' ', '+')}",
                    "result_selector": ".s-post-summary, .question-summary, .search-result",
                    "title_selector": "h3 a, .question-hyperlink, .result-link a",
                    "link_selector": "h3 a, .question-hyperlink, .result-link a",
                    "snippet_selector": ".s-post-summary--content-excerpt, .excerpt, .result-excerpt",
                    "base_url": "https://stackoverflow.com"
                },
                "github": {
                    "search_url": f"https://github.com/search?q={query.replace(' ', '+')}&type=repositories",
                    "result_selector": ".repo-list-item, .hx_hit-repo, .Code-searchResults-result",
                    "title_selector": "a.v-align-middle, .hx_hit-repo-path, h3 a",
                    "link_selector": "a.v-align-middle, .hx_hit-repo-path, h3 a",
                    "snippet_selector": "p.mb-1, .hx_hit-repo-desc, .description",
                    "base_url": "https://github.com"
                },
                "mdn": {
                    "search_url": f"https://developer.mozilla.org/en-US/search?q={query.replace(' ', '+')}",
                    "result_selector": ".result, .search-result, .search-results-entry",
                    "title_selector": ".result-title, h3 a, .entry-title",
                    "link_selector": ".result-title a, h3 a, .entry-title a",
                    "snippet_selector": ".result-excerpt, .search-item-excerpt, .entry-summary",
                    "base_url": "https://developer.mozilla.org"
                },
                "freecodecamp": {
                    "search_url": f"https://www.freecodecamp.org/news/?s={query.replace(' ', '+')}",
                    "result_selector": "article, .article-card, .post-card",
                    "title_selector": "h2.title, .post-card-title, .post-title",
                    "link_selector": "h2.title a, .post-card-title a",
                    "snippet_selector": ".excerpt, .post-card-excerpt, .post-excerpt",
                    "base_url": "https://www.freecodecamp.org"
                },
                "dev_to": {
                    "search_url": f"https://dev.to/search?q={query.replace(' ', '+')}",
                    "result_selector": ".crayons-story, .search-results-item, .single-article",
                    "title_selector": "h2 a, .crayons-story__title a, .title a",
                    "link_selector": "h2 a, .crayons-story__title a",
                    "snippet_selector": ".crayons-story__snippet, .body, .content",
                    "base_url": "https://dev.to"
                },
                "python_docs": {
                    "search_url": f"https://docs.python.org/3/search.html?q={query.replace(' ', '+')}&check_keywords=yes&area=default",
                    "result_selector": "ul.search li, .search-result, .search-item",
                    "title_selector": "a, .search-title, .result-title",
                    "link_selector": "a, .search-title a",
                    "snippet_selector": ".context, .search-summary, .result-context",
                    "base_url": "https://docs.python.org/3"
                }
            }
            
            source_config = tech_source_configs.get(source_name)
            if not source_config:
                return []
                
            self.driver.get(source_config["search_url"])
            time.sleep(3)  # Wait for page to load
            
            # Find result items
            results_found = []
            try:
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, source_config["result_selector"])
                
                # Process up to 3 results per technical source
                for result in result_elements[:3]:
                    try:
                        # Extract title
                        title = None
                        for title_selector in source_config["title_selector"].split(", "):
                            try:
                                title_elem = result.find_element(By.CSS_SELECTOR, title_selector)
                                if title_elem and title_elem.text.strip():
                                    title = title_elem.text.strip()
                                    break
                            except:
                                continue
                                
                        if not title:
                            continue
                        
                        # Extract link
                        link = None
                        for link_selector in source_config["link_selector"].split(", "):
                            try:
                                link_elem = result.find_element(By.CSS_SELECTOR, link_selector)
                                if link_elem:
                                    link = link_elem.get_attribute("href")
                                    if link:
                                        break
                            except:
                                continue
                                
                        if not link:
                            # Try to find any link in the result
                            links = result.find_elements(By.TAG_NAME, "a")
                            if links:
                                link = links[0].get_attribute("href")
                            else:
                                continue
                                
                        # Make sure it's an absolute URL
                        if link and link.startswith('/'):
                            link = source_config["base_url"] + link
                            
                        # Extract snippet if available
                        snippet = None
                        for snippet_selector in source_config["snippet_selector"].split(", "):
                            try:
                                snippet_elem = result.find_element(By.CSS_SELECTOR, snippet_selector)
                                if snippet_elem and snippet_elem.text.strip():
                                    snippet = snippet_elem.text.strip()
                                    break
                            except:
                                continue
                                
                        # Format source name for display
                        display_name = source_name.replace('_', ' ').title()
                        
                        # If we have a link, try to get full content
                        if snippet and len(snippet) > 150:
                            # If snippet is substantial, use it instead of making another request
                            content = snippet
                        else:
                            # Otherwise get full content
                            content = self.scrape_news_content(link)
                            
                        results_found.append({
                            'title': title,
                            'link': link,
                            'source': f"{display_name} (Technical)",
                            'time': f"Technical Resource - {datetime.now().strftime('%B %d, %Y')}",
                            'content': content
                        })
                        
                    except Exception as e:
                        print(f"Error extracting result from {source_name}: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error finding results in {source_name}: {e}")
            
            return results_found
            
        except Exception as e:
            print(f"Error in scrape_technical_source for {source_name}: {e}")
            return []

    def is_technical_query(self, query):
        """Determine if a query is likely to be technical in nature"""
        # Common technical keywords and patterns
        technical_keywords = [
            'programming', 'code', 'algorithm', 'function', 'variable', 
            'python', 'java', 'javascript', 'html', 'css', 'sql', 'database',
            'api', 'framework', 'library', 'syntax', 'error', 'debug',
            'compiler', 'interpreter', 'runtime', 'exception', 'stack',
            'frontend', 'backend', 'fullstack', 'web development',
            'data structure', 'recursion', 'iteration', 'loop', 'condition',
            'class', 'object', 'method', 'property', 'inheritance',
            'polymorphism', 'encapsulation', 'abstraction', 'interface',
            'docker', 'kubernetes', 'aws', 'cloud', 'devops', 'ci/cd',
            'git', 'github', 'version control', 'linux', 'terminal', 
            'command line', 'bash', 'shell', 'script', 'react', 'angular',
            'vue', 'node', 'express', 'flask', 'django', 'spring', 'boot'
        ]
        
        # Check if query contains technical keywords
        query_lower = query.lower()
        for keyword in technical_keywords:
            if keyword in query_lower:
                return True
                
        # Check for patterns that indicate technical questions
        technical_patterns = [
            r'how to (implement|code|program|create|develop)',
            r'what is [a-z\s]+ (in|for) (programming|development|coding)',
            r'(fix|resolve|debug) [a-z\s]+ (error|bug|issue|exception)',
            r'(best|recommended) (practice|way) to [a-z\s]+ in',
            r'difference between [a-z\s]+ and [a-z\s]+',
            r'(example|tutorial) (of|for) [a-z\s]+',
            r'(implement|create) [a-z\s]+ (using|with) [a-z\s]+'
        ]
        
        for pattern in technical_patterns:
            if re.search(pattern, query_lower):
                return True
                
        return False

    def scrape_news(self, query):
        try:
            # Add time parameter for fresh results
            current_time = datetime.now()
            
            # List of major Indian news sources to directly scrape
            indian_news_sources = [
                "times_of_india",
                "hindustan_times",
                "the_hindu",
                "ndtv",
                "india_today"
            ]
            
            # List of technical sources to scrape for technical queries
            technical_sources = [
                "geeksforgeeks",
                "javatpoint",
                "tutorialspoint",
                "w3schools",
                "stackoverflow",
                "github",
                "mdn",
                "freecodecamp",
                "dev_to",
                "python_docs"
            ]
            
            all_results = []
            
            # Check if this is a technical query
            is_tech_query = self.is_technical_query(query)
            
            # For technical queries, prioritize technical sources
            if is_tech_query:
                print(f"Detected technical query: '{query}' - prioritizing technical sources")
                
                # Randomize the order of technical sources to vary results
                random.shuffle(technical_sources)
                
                # Scrape from technical sources
                for source in technical_sources[:5]:  # Limit to 5 sources to avoid too many requests
                    print(f"Scraping technical content from {source}...")
                    tech_results = self.scrape_technical_source(source, query)
                    
                    if tech_results:
                        all_results.extend(tech_results)
                        print(f"Found {len(tech_results)} results from {source}")
                        
                    # If we have enough results, stop searching
                    if len(all_results) >= 10:
                        break
                        
            # If it's a general news query, include direct scraping from top sources
            is_general_news_query = False
            general_news_keywords = ["today news", "latest news", "india news", "current news", 
                                     "breaking news", "top news", "recent news", "headlines"]
                                     
            for keyword in general_news_keywords:
                if keyword in query.lower():
                    is_general_news_query = True
                    break
            
            # For general news queries, directly scrape from top sources
            if is_general_news_query:
                print("Detected general news query - scraping directly from top sources")
                # Randomize the order of sources to vary results
                random.shuffle(indian_news_sources)
                
                # Scrape from each source
                for source in indian_news_sources:
                    print(f"Scraping directly from {source}...")
                    source_results = self.scrape_direct_from_source(source)
                    if source_results:
                        all_results.extend(source_results)
                        print(f"Found {len(source_results)} articles from {source}")
                    
                    # If we have enough results, stop scraping
                    if len(all_results) >= 20:
                        break
            
            # Handle "today news" query specifically
            if query.lower() == "today news" or query.lower() == "latest news":
                query = "latest news today"
                # Add date to ensure freshness
                query += f" {current_time.strftime('%B %d %Y')}"
            
            # Always add freshness indicators to query
            if "latest" not in query.lower() and "recent" not in query.lower():
                query += " latest"

            # Encode the query for URL
            encoded_query = query.replace(' ', '+')
            
            # Add specific site search for major news sources if we need more results
            if len(all_results) < 20:
                # Define sources to search based on query type
                if is_tech_query:
                    search_sites = [
                        "geeksforgeeks.org",
                        "javatpoint.com",
                        "tutorialspoint.com",
                        "w3schools.com",
                        "stackoverflow.com",
                        "github.com",
                        "developer.mozilla.org",
                        "freecodecamp.org",
                        "dev.to",
                        "docs.python.org"
                    ]
                else:
                    search_sites = [
                        "timesofindia.indiatimes.com",
                        "hindustantimes.com", 
                        "thehindu.com",
                        "ndtv.com",
                        "indiatoday.in",
                        "indianexpress.com",
                        "news18.com",
                        "economictimes.indiatimes.com",
                        "bbc.com/news/world/asia/india",
                        "livemint.com"
                    ]
                
                # Search specifically on these sites
                for site in search_sites[:5]:  # Limit to 5 sites
                    site_query = f"{encoded_query} site:{site}"
                    search_url = f"https://www.google.com/search?q={site_query}&tbm=nws"
                    print(f"Searching for {'technical content' if is_tech_query else 'news'} on {site}...")
                    
                    self.driver.get(search_url)
                    time.sleep(2)  # Shorter wait to avoid timeouts
                    
                    # Try multiple possible selectors for news items
                    selectors = ['.dbsr', 'g', '.mnr-c', 'article', '.ddle5', '.WlydOe', '.n6jlAc']
                    news_items = []
                    
                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements and len(elements) > 0:
                                news_items = elements[:5]  # Limit to 5 news items per site
                                print(f"Found {len(news_items)} items from {site}")
                                break
                        except:
                            continue
                    
                    # Process the news items
                    for item in news_items:
                        try:
                            title = None
                            link = None
                            source = None
                            time_posted = None
                            
                            # Extract title with expanded selectors
                            for title_selector in ['div.nDgy9d', 'h3', 'h4', '.JheGif', '.DY5T1d', '.vF3A6c']:
                                try:
                                    title_elem = item.find_element(By.CSS_SELECTOR, title_selector)
                                    if title_elem:
                                        title = title_elem.text
                                        break
                                except:
                                    continue
                                    
                            if not title:
                                title = item.text.split('\n')[0] if item.text else "Untitled Article"
                                
                            # Extract link
                            for link_selector in ['a', '.WlydOe', '.DY5T1d', '.tHmfQe']:
                                try:
                                    link_elem = item.find_element(By.CSS_SELECTOR, link_selector)
                                    if link_elem:
                                        link = link_elem.get_attribute('href')
                                        break
                                except:
                                    continue
                                    
                            if not link:
                                links = item.find_elements(By.TAG_NAME, 'a')
                                if links:
                                    link = links[0].get_attribute('href')
                                else:
                                    continue
                                    
                            # Set source from the site we're searching
                            source = site.replace("www.", "").replace(".com", "").replace(".in", "").replace(".org", "").title()
                            if is_tech_query:
                                source += " (Technical)"
                                
                            # Extract time posted
                            for time_selector in ['.WG9SHc span', '.ZE0LJd', '.LfVVr', 'time', '.OSrXXb']:
                                try:
                                    time_elem = item.find_element(By.CSS_SELECTOR, time_selector)
                                    if time_elem:
                                        time_posted = time_elem.text
                                        break
                                except:
                                    continue
                                    
                            time_posted = time_posted or f"Recent - {current_time.strftime('%B %d, %Y')}"
                            
                            # Get content
                            content = self.scrape_news_content(link)
                            
                            # Check for duplicates
                            duplicate = False
                            for existing in all_results:
                                if title.lower() == existing['title'].lower():
                                    duplicate = True
                                    break
                                    
                            if not duplicate:
                                all_results.append({
                                    'title': title,
                                    'link': link,
                                    'source': source,
                                    'time': time_posted,
                                    'content': content
                                })
                                
                            # If we have enough results, break
                            if len(all_results) >= 20:
                                break
                                
                        except Exception as e:
                            print(f"Error processing item from {site}: {e}")
                            continue
                    
                    # If we have enough results, break
                    if len(all_results) >= 20:
                        break
            
            # If we still need more results, use the general approach
            if len(all_results) < 15:
                # Try multiple search engines for more diverse sources
                search_urls = [
                    f"https://www.google.com/search?q={encoded_query}&tbm=nws",
                    f"https://news.google.com/search?q={encoded_query}&hl=en-US"
                ]
                
                for search_url in search_urls:
                    self.driver.get(search_url)
                    # Wait for page to load
                    time.sleep(3)
                    
                    # Try multiple possible selectors for news items
                    selectors = [
                        '.dbsr', 'g', '.mnr-c', 'article', '.ddle5', '.WlydOe', '.n6jlAc',
                        '.NiLAwe', '.DY5T1d', '.qLBgNd', '.IBr9hb'
                    ]
                    news_items = []

                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements and len(elements) > 0:
                                news_items = elements[:20]
                                break
                        except:
                            continue

                    if not news_items:
                        continue
                    
                    # Process the news items
                    for item in news_items:
                        try:
                            # Extract title, link, source, time_posted similar to above
                            title = None
                            link = None
                            source = None
                            time_posted = None
                            
                            # Extract title with expanded selectors
                            for title_selector in ['div.nDgy9d', 'h3', 'h4', '.JheGif', '.DY5T1d', '.vF3A6c', '.DFN7ze', '.RD0gLb']:
                                try:
                                    title_elem = item.find_element(By.CSS_SELECTOR, title_selector)
                                    if title_elem:
                                        title = title_elem.text
                                        break
                                except:
                                    continue

                            if not title:
                                title = item.text.split('\n')[0] if item.text else "Untitled Article"

                            # Extract link with expanded selectors
                            for link_selector in ['a', '.WlydOe', '.DY5T1d', '.tHmfQe', '.VDXfz', '.SFllF']:
                                try:
                                    link_elem = item.find_element(By.CSS_SELECTOR, link_selector)
                                    if link_elem:
                                        link = link_elem.get_attribute('href')
                                        break
                                except:
                                    continue

                            if not link:
                                links = item.find_elements(By.TAG_NAME, 'a')
                                if links:
                                    link = links[0].get_attribute('href')
                                else:
                                    continue

                            # Extract source with expanded selectors
                            for source_selector in ['.XTjFC.WF4CUc', '.UPmit', '.CEMjEf', '.TVtOme', 'span', '.NUnG9d', '.wEwyrc', '.vr1PYe']:
                                try:
                                    source_elem = item.find_element(By.CSS_SELECTOR, source_selector)
                                    if source_elem:
                                        source = source_elem.text
                                        break
                                except:
                                    continue

                            source = source or "News Source"

                            # Extract time posted
                            for time_selector in ['.WG9SHc span', '.ZE0LJd', '.LfVVr', 'time', '.OSrXXb']:
                                try:
                                    time_elem = item.find_element(By.CSS_SELECTOR, time_selector)
                                    if time_elem:
                                        time_posted = time_elem.text
                                        break
                                except:
                                    continue

                            time_posted = time_posted or f"Recent - {current_time.strftime('%B %d, %Y')}"
                            
                            content = self.scrape_news_content(link)
                            
                            # Check for duplicates
                            duplicate = False
                            for existing in all_results:
                                if title.lower() == existing['title'].lower():
                                    duplicate = True
                                    break
                                
                            if not duplicate:
                                all_results.append({
                                    'title': title,
                                    'link': link,
                                    'source': source,
                                    'time': time_posted,
                                    'content': content
                                })
                                
                            # If we have enough results, break early
                            if len(all_results) >= 20:
                                break
                                
                        except Exception as e:
                            print(f"Error scraping news item: {e}")
                            continue
                    
                    # If we have enough results, don't try other search engines
                    if len(all_results) >= 15:
                        break
            
            # Sort results by recency and relevance
            try:
                def get_source_score(item):
                    # Technical sources get higher priority for technical queries
                    if is_tech_query and "(Technical)" in item.get('source', ''):
                        return 0  # Highest priority
                        
                    source_lower = item.get('source', '').lower()
                    # List of preferred sources
                    if any(preferred in source_lower for preferred in [
                        'geeksforgeeks', 'javatpoint', 'tutorialspoint', 'w3schools', 'stackoverflow',
                        'github', 'mdn', 'mozilla', 'freecodecamp', 'python', 
                        'times of india', 'hindustan', 'hindu', 'ndtv', 'india today'
                    ]):
                        return 1  # High priority
                    return 2  # Normal priority
                
                def get_recency_score(item):
                    time_str = item['time'].lower()
                    if "min" in time_str:
                        return 1
                    elif "hour" in time_str:
                        return 2
                    elif "today" in time_str:
                        return 3
                    elif "yesterday" in time_str:
                        return 4
                    elif "day" in time_str:
                        return 5
                    elif "week" in time_str:
                        return 6
                    else:
                        return 7
                
                # Sort first by source quality then by recency
                all_results.sort(key=lambda x: (get_source_score(x), get_recency_score(x)))
            except:
                # If sorting fails, leave as is
                pass
                
            print(f"Total unique items found: {len(all_results)}")
            
            # Limit to 20 results maximum
            return all_results[:20]

        except Exception as e:
            print(f"Error in scrape_news: {e}")
            return []
        finally:
            self.driver.quit()
