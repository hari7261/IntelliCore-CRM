document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const deepSearchToggle = document.getElementById('deep-search-toggle');
    const modeLabel = document.getElementById('mode-label');
    const newChatButton = document.getElementById('new-chat');
    const chatHistory = document.getElementById('chat-history');
    const chatModal = document.getElementById('chat-modal');
    const closeModal = chatModal.querySelector('.close');
    const chatTitleInput = document.getElementById('chat-title-input');
    const saveChatButton = document.getElementById('save-chat');
    const deleteChatButton = document.getElementById('delete-chat');
    const conversationTitle = document.getElementById('conversation-title');
    const sourcesModal = document.getElementById('sources-modal');
    const closeSourcesModal = sourcesModal.querySelector('.close');
    const sourcesContent = document.getElementById('sources-content');

    // State
    let currentConversationId = null;
    let isDeepSearch = false;
    let isLoading = false;

    // Initialize
    loadConversations();
    setupEventListeners();

    function setupEventListeners() {
        // Send message on button click or Enter key
        sendButton.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !isLoading) {
                sendMessage();
            }
        });

        // Toggle deep search mode
        deepSearchToggle.addEventListener('change', function() {
            isDeepSearch = this.checked;
            modeLabel.textContent = isDeepSearch ? 'Deep Search' : 'Basic Chat';
        });

        // New chat button
        newChatButton.addEventListener('click', startNewConversation);

        // Chat management modal
        closeModal.addEventListener('click', () => chatModal.style.display = 'none');
        saveChatButton.addEventListener('click', saveConversation);
        deleteChatButton.addEventListener('click', deleteConversation);

        // Sources modal
        closeSourcesModal.addEventListener('click', () => sourcesModal.style.display = 'none');

        // Close modals when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === chatModal) {
                chatModal.style.display = 'none';
            }
            if (event.target === sourcesModal) {
                sourcesModal.style.display = 'none';
            }
        });
    }

    function loadConversations() {
        fetch('/api/conversations')
            .then(response => response.json())
            .then(conversations => {
                chatHistory.innerHTML = '';
                conversations.forEach(conv => {
                    const convElement = document.createElement('div');
                    convElement.className = 'conversation-item';
                    convElement.dataset.id = conv.id;
                    
                    convElement.innerHTML = `
                        <div class="conversation-title">${conv.title}</div>
                        <div class="conversation-actions">
                            <button class="edit-chat" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    `;
                    
                    convElement.addEventListener('click', function() {
                        loadConversation(conv.id);
                    });
                    
                    const editButton = convElement.querySelector('.edit-chat');
                    editButton.addEventListener('click', function(e) {
                        e.stopPropagation();
                        openChatModal(conv.id, conv.title);
                    });
                    
                    chatHistory.appendChild(convElement);
                });
            })
            .catch(error => console.error('Error loading conversations:', error));
    }

    function loadConversation(conversationId) {
        fetch(`/api/conversation/${conversationId}`)
            .then(response => response.json())
            .then(data => {
                // Clear current chat
                chatMessages.innerHTML = '';
                currentConversationId = conversationId;
                conversationTitle.textContent = data.title;
                
                // Update active state in sidebar
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('active');
                    if (item.dataset.id === conversationId.toString()) {
                        item.classList.add('active');
                    }
                });
                
                // Add messages to chat
                data.messages.forEach(message => {
                    addMessageToUI(message.content, message.is_user, message.sources);
                });
                
                // Scroll to bottom
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => console.error('Error loading conversation:', error));
    }

    function startNewConversation() {
        currentConversationId = null;
        chatMessages.innerHTML = '';
        conversationTitle.textContent = 'New Conversation';
        userInput.value = '';
        
        // Remove active state from all conversations
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (!message || isLoading) return;
        
        // Add user message to UI
        addMessageToUI(message, true);
        userInput.value = '';
        isLoading = true;
        
        // Show loading indicator in send button
        sendButton.innerHTML = '<div class="loading"></div>';
        sendButton.disabled = true;
        
        // Send to backend
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                deep_search: isDeepSearch,
                conversation_id: currentConversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            currentConversationId = data.conversation_id;
            addMessageToUI(data.response, false, data.sources);
            
            // Reload conversations to update the list
            loadConversations();
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToUI("Sorry, I encountered an error processing your request.", false);
        })
        .finally(() => {
            isLoading = false;
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            sendButton.disabled = false;
        });
    }

    function addMessageToUI(content, isUser, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
        messageDiv.innerHTML = content;
        
        // Add sources button if available
        if (sources && !isUser) {
            const sourcesButton = document.createElement('button');
            sourcesButton.className = 'view-sources-btn';
            sourcesButton.textContent = 'View Sources';
            sourcesButton.addEventListener('click', () => showSources(sources));
            
            const sourcesContainer = document.createElement('div');
            sourcesContainer.className = 'message-sources';
            sourcesContainer.appendChild(sourcesButton);
            
            messageDiv.appendChild(sourcesContainer);
        }
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function openChatModal(conversationId, title) {
        currentConversationId = conversationId;
        chatTitleInput.value = title;
        chatModal.style.display = 'block';
    }

    function saveConversation() {
        const newTitle = chatTitleInput.value.trim();
        if (!newTitle || !currentConversationId) return;
        
        fetch(`/api/conversation/${currentConversationId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                conversationTitle.textContent = newTitle;
                chatModal.style.display = 'none';
                loadConversations();
            }
        })
        .catch(error => console.error('Error updating conversation:', error));
    }

    function deleteConversation() {
        if (!currentConversationId) return;
        
        if (confirm('Are you sure you want to delete this conversation?')) {
            fetch(`/api/conversation/${currentConversationId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    chatModal.style.display = 'none';
                    startNewConversation();
                    loadConversations();
                }
            })
            .catch(error => console.error('Error deleting conversation:', error));
        }
    }

    function showSources(sources) {
        if (!sources) return;
        
        sourcesContent.innerHTML = '';
        
        if (Array.isArray(sources)) {
            sources.forEach((source, index) => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                
                sourceItem.innerHTML = `
                    <div class="source-title">${source.title || 'Untitled Source'}</div>
                    ${source.source ? `<div class="source-meta">Source: ${source.source}</div>` : ''}
                    ${source.time ? `<div class="source-meta">Time: ${source.time}</div>` : ''}
                    <div class="source-content">${source.content || 'No content available'}</div>
                    ${source.link ? `<a href="${source.link}" target="_blank" class="source-link">View original</a>` : ''}
                `;
                
                sourcesContent.appendChild(sourceItem);
            });
        } else if (typeof sources === 'object') {
            // Handle single source object
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            
            sourceItem.innerHTML = `
                <div class="source-title">${sources.title || 'Untitled Source'}</div>
                ${sources.source ? `<div class="source-meta">Source: ${sources.source}</div>` : ''}
                ${sources.time ? `<div class="source-meta">Time: ${sources.time}</div>` : ''}
                <div class="source-content">${sources.content || 'No content available'}</div>
                ${sources.link ? `<a href="${sources.link}" target="_blank" class="source-link">View original</a>` : ''}
            `;
            
            sourcesContent.appendChild(sourceItem);
        }
        
        sourcesModal.style.display = 'block';
    }
});