# Smart CRM with AI-Powered Research and Intelligent Responses

![CRM System Banner](https://via.placeholder.com/1200x300/2c3e50/FFFFFF?text=Smart+CRM+with+AI+Research)

## 🌟 Overview

This advanced CRM system combines intelligent web scraping with AI-powered responses to provide comprehensive and accurate information on any query. The system can handle both general news queries and technical programming questions by dynamically searching and aggregating information from trusted sources.

### Key Features

- **AI-Powered Responses**: Uses Google's Gemini 2.0 to generate well-structured, contextual responses
- **Web Scraping Engine**: Intelligent data collection from diverse sources including:
  - **News Sources**: Times of India, Hindustan Times, The Hindu, NDTV, India Today, and more
  - **Technical Sources**: GeeksforGeeks, JavaTPoint, StackOverflow, W3Schools, GitHub, MDN, and more
- **Query Understanding**: Automatically detects whether a query is technical or news-related
- **Conversation History**: Maintains a history of all interactions for future reference
- **Deep Search Mode**: Provides detailed, source-backed responses for important queries
- **Modern Web Interface**: Clean UI with support for markdown formatting in responses

## 🚀 Technical Architecture

### Components

1. **Flask Web Application** (`app.py`)
   - Handles HTTP requests and user interface
   - Manages conversations and message history
   - Integrates with Gemini API for AI responses

2. **Web Scraper** (`scraper.py`)
   - Intelligent source selection based on query type
   - Multi-source data collection with selenium and BeautifulSoup
   - Content extraction from various websites
   - Deduplication and relevance sorting

3. **Database Models** (SQLite with SQLAlchemy)
   - Conversations
   - Messages with source tracking  
   - Search history

4. **AI Integration** (Google Gemini 2.0)
   - Contextual response generation
   - Source citation and formatting

## 📋 Features In Detail

### Intelligent Search System

The search system automatically detects the type of query and selects appropriate sources:

- **News Queries**: For current events, latest news, etc.
  - Direct scraping from major Indian newspapers
  - Google News integration
  - Time-based relevance scoring

- **Technical Queries**: For programming, development, and technical questions
  - Specialized scraping from developer resources
  - Pattern matching to detect technical intent
  - Resource quality prioritization

### Response Generation

The system processes scraped information through Google's Gemini AI to:

1. Summarize key findings
2. Structure information logically
3. Cite sources appropriately
4. Format response for readability
5. Provide contextual insights

### User Interface Features

- Conversation management (create, view, delete)
- Deep search toggle for more comprehensive research
- Rich text formatting in responses
- Source citation with links
- Mobile-responsive design

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+ 
- Chrome browser (for Selenium)
- Required Python packages

### Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd CRM-2
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API key:
   - Create a `config.py` file with your Gemini API key:
   ```python
   class Config:
       SECRET_KEY = "your-secret-key"
       SQLALCHEMY_DATABASE_URI = "sqlite:///crm.db"
       GEMINI_API_KEY = "your-gemini-api-key"
       SQLALCHEMY_TRACK_MODIFICATIONS = False
   ```

4. Initialize the database:
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   >>> exit()
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## 💡 Usage Guide

### Starting a Conversation

1. Enter your query in the input field at the bottom of the screen
2. Toggle "Deep Search" if you want comprehensive, source-backed research
3. Click "Send" or press Enter

### Query Types

- **General News**: "What's happening in Ukraine?", "Today's top news", "Latest updates on climate change"
- **Technical Questions**: "How to implement binary search in Python?", "Explain React hooks", "Java vs Python performance"

### Viewing History

- All conversations are saved and accessible from the sidebar
- Click on any past conversation to view the full exchange
- Delete conversations using the trash icon

## 🔧 Customization

### Adding New Sources

To add new sources, modify the configuration dictionaries in `scraper.py`:

- For news sources, add to the `source_configs` dictionary
- For technical sources, add to the `tech_source_configs` dictionary

Each source requires:
- URL template
- CSS selectors for articles/results
- Selectors for titles, links, etc.

### Modifying AI Response Format

Adjust the prompt templates in `app.py` to change how responses are structured.

## 📈 Future Enhancements

- Multi-user support with authentication
- API integration for third-party applications
- Enhanced data visualization for complex topics
- Voice interface for queries and responses
- PDF/document attachment analysis
- Scheduled monitoring for specific topics

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- Google Gemini API for powering the AI responses
- Selenium and BeautifulSoup for web scraping capabilities
- Flask and SQLAlchemy for the application framework
- All the news and technical sources that provide valuable information

---

Built with ❤️ using Python, Flask, and Google Gemini AI