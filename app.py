from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import google.generativeai as genai
from datetime import datetime
from scraper import WebScraper
import json
import re
from config import Config
from models import db, Conversation, Message, SearchHistory

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Initialize Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

def format_ai_response(text):
    """
    Enhanced formatting for AI responses with proper HTML structure for the chat interface
    Includes special handling for source citations and better visual formatting
    """
    # Convert markdown to HTML-like structure for the frontend
    formatted_lines = []
    in_list = False
    in_code = False
    
    # Split into lines and process each one
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        
        # Skip empty lines (we'll handle spacing later)
        if not line:
            continue
            
        # Headers (## Header)
        if line.startswith('## '):
            if in_list:
                formatted_lines.append('</ul>' if not line.startswith('- ') else '')
                in_list = False
            formatted_lines.append(f'<h3 class="ai-response-heading">{line[3:]}</h3>')
            
        # Subheaders (### Subheader)
        elif line.startswith('### '):
            if in_list:
                formatted_lines.append('</ul>' if not line.startswith('- ') else '')
                in_list = False
            formatted_lines.append(f'<h4 class="ai-response-subheading">{line[4:]}</h4>')
            
        # Bullet points (- or *)
        elif line.startswith('- ') or line.startswith('* '):
            if not in_list:
                formatted_lines.append('<ul>')
                in_list = True
            formatted_lines.append(f'<li>{line[2:]}</li>')
            
        # Numbered lists (1. 2. etc)
        elif re.match(r'^\d+\.\s', line):
            if not in_list:
                formatted_lines.append('<ol>')
                in_list = True
            formatted_lines.append(f'<li>{line[line.find(" ")+1:]}</li>')
            
        # Code blocks (```)
        elif line.startswith('```'):
            if in_code:
                formatted_lines.append('</pre></code>')
                in_code = False
            else:
                formatted_lines.append('<code><pre>')
                in_code = True
                  # Regular paragraphs
        else:
            if in_list:
                formatted_lines.append('</ul>' if not line.startswith('- ') else '</ol>' if re.match(r'^\d+\.\s', line) else '')
                in_list = False
            if in_code:
                formatted_lines.append(line)
            else:
                # Highlight source citations [Source X]
                line_with_citations = re.sub(
                    r'\[Source\s*(\d+)\]', 
                    r'<span class="source-citation">[Source \1]</span>', 
                    line
                )
                
                # Split long paragraphs into shorter ones for readability
                if len(line) > 120:
                    parts = [line_with_citations[i:i+120] for i in range(0, len(line_with_citations), 120)]
                    for part in parts:
                        formatted_lines.append(f'<p>{part}</p>')
                else:
                    formatted_lines.append(f'<p>{line_with_citations}</p>')
    
    # Close any open tags
    if in_list:
        formatted_lines.append('</ul>')
    if in_code:
        formatted_lines.append('</pre></code>')
    
    # Combine with line breaks for readability
    return '\n'.join(formatted_lines)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    return jsonify([{
        'id': conv.id,
        'title': conv.title,
        'updated_at': conv.updated_at.strftime('%Y-%m-%d %H:%M'),
        'is_deep_search': conv.is_deep_search
    } for conv in conversations])

@app.route('/api/conversation/<int:conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    try:
        # Get conversation with error handling
        conversation = Conversation.query.get_or_404(conversation_id)
        
        # Paginated messages query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        messages = Message.query\
            .filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at)\
            .paginate(page=page, per_page=per_page, error_out=False)
            
        return jsonify({
            'conversation': {
                'id': conversation.id,
                'title': conversation.title,
                'created_at': conversation.created_at.isoformat(),
                'is_deep_search': conversation.is_deep_search
            },
            'messages': [{
                'id': msg.id,
                'content': msg.content,
                'is_user': msg.is_user,
                'created_at': msg.created_at.isoformat(),
                'sources': json.loads(msg.sources) if msg.sources else None
            } for msg in messages.items],
            'pagination': {
                'page': messages.page,
                'per_page': messages.per_page,
                'total_pages': messages.pages,
                'total_items': messages.total
            }
        })
    except Exception as e:
        app.logger.error(f"Error fetching conversation {conversation_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve conversation'}), 500

@app.route('/api/conversation/<int:conversation_id>', methods=['PUT'])
def update_conversation(conversation_id):
    data = request.json
    conversation = Conversation.query.get_or_404(conversation_id)
    
    if 'title' in data:
        conversation.title = data['title']
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/conversation/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    db.session.delete(conversation)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.json
    message = data['message'].strip()
    is_deep_search = data.get('deep_search', False)
    conversation_id = data.get('conversation_id')
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Create or get conversation
    if conversation_id:
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
    else:
        conversation = Conversation(
            title=message[:50],
            is_deep_search=is_deep_search
        )
        db.session.add(conversation)
        db.session.commit()
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        content=message,
        is_user=True
    )
    db.session.add(user_message)
    # Generate response
    try:
        scraped_data = None
        if is_deep_search:
            try:
                # Perform deep search
                app.logger.info(f"Starting deep search for: {message}")
                scraper = WebScraper()
                scraped_data = scraper.scrape_news(message)
                app.logger.info(f"Deep search completed. Found {len(scraped_data)} sources.")
                
                if not scraped_data:
                    app.logger.warning("Deep search returned no results")
                    # Fall back to regular search if no results found
                    prompt = (
                        f"Please provide a clear, structured response to: '{message}'\n\n"
                        "Note: I tried to search for relevant information but couldn't find any specific sources.\n\n"
                        "Organize your answer with:\n"
                        "## Summary\n"
                        "- Key points\n\n"
                        "## Explanation\n"
                        "1. Step-by-step details\n"
                        "2. Supporting information\n\n"
                        "## Conclusion\n"
                        "- Final thoughts\n"
                        "- Recommendations if applicable"
                    )
                else:                    # Save search history
                    search_history = SearchHistory(
                        conversation_id=conversation.id,
                        query=message,
                        sources=json.dumps(scraped_data)
                    )
                    db.session.add(search_history)
                    
                    # Enhance each source with metadata for better context
                    enriched_sources = []
                    for i, item in enumerate(scraped_data):
                        source_number = i + 1
                        source_info = {
                            "number": source_number,
                            "title": item['title'],
                            "source": item['source'],
                            "time": item['time'],
                            "content_preview": item['content'][:3000] if len(item['content']) > 3000 else item['content']
                        }
                        enriched_sources.append(source_info)
                    
                    # Prepare prompt for Gemini with clear structure request and source metadata
                    sources_text = "\n\n".join(
                        f"Source {src['number']}:\nTitle: {src['title']}\nPublisher: {src['source']}\nDate: {src['time']}\nContent: {src['content_preview']}..."
                        for src in enriched_sources
                    )
                    
                    prompt = (
                        f"You are tasked with providing a comprehensive response about: '{message}'\n\n"
                        f"Using the following sources:\n{sources_text}\n\n"
                        "Your response should be thorough, well-structured, and specifically reference information from the sources provided.\n\n"
                        "Structure your response as follows:\n\n"
                        "## Key Findings\n"
                        "- Provide 3-5 bullet points summarizing the most important information\n"
                        "- Highlight the key facts relevant to the query\n\n"
                        "## Detailed Analysis\n"
                        "1. First major point with supporting evidence\n"
                        "2. Second major point with supporting evidence\n"
                        "3. Third major point with supporting evidence\n\n"
                        "## Additional Insights\n"
                        "- Include any other relevant information\n"
                        "- Note any contradictions or nuances across sources\n\n"
                        "## Sources\n"
                        "- List the key sources that informed your response\n\n"
                        "When referencing information, cite the sources using the format [Source X] where X is the source number."
                    )
            except Exception as e:
                app.logger.error(f"Error in deep search: {str(e)}")
                # Fall back to regular search if deep search fails
                prompt = (
                    f"Please provide a clear, structured response to: '{message}'\n\n"
                    "Note: I tried to search for relevant information but encountered technical issues.\n\n"
                    "Organize your answer with:\n"
                    "## Summary\n"
                    "- Key points\n\n"
                    "## Explanation\n"
                    "1. Step-by-step details\n"
                    "2. Supporting information\n\n"
                    "## Conclusion\n"
                    "- Final thoughts\n"
                    "- Recommendations if applicable"
                )
        else:
            # For basic chat, still request structured response
            prompt = (
                f"Please provide a clear, structured response to: '{message}'\n\n"
                "Organize your answer with:\n"
                "## Summary\n"
                "- Key points\n\n"
                "## Explanation\n"
                "1. Step-by-step details\n"
                "2. Supporting information\n\n"
                "## Conclusion\n"
                "- Final thoughts\n"
                "- Recommendations if applicable"
            )
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        response_text = format_ai_response(response.text)
        
        # Save AI response
        ai_message = Message(
            conversation_id=conversation.id,
            content=response_text,
            is_user=False,
            sources=json.dumps(scraped_data) if scraped_data else None
        )
        db.session.add(ai_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'response': response_text,
            'conversation_id': conversation.id,
            'sources': scraped_data
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'response': "<p>Sorry, I encountered an error processing your request.</p>"
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)