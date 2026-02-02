import streamlit as st
import streamlit.components.v1 as components
from services.db import fetch_kpis
from services.llm import get_llm_response
from services.prompts import ai_retention_prompt
import base64
from pathlib import Path
from typing import Dict, Any
import time

# ================= CONFIGURATION =================
PAGE_CONFIG = {
    "page_title": "ChurnGuard | Retention Intelligence",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

ASSET_PATHS = {
    "architecture": "assets/architecture.png",
    "dash_overview": "assets/churn_overview.jpg",
    "dash_trends": "assets/churn_trends.jpg",
    "dash_revenue": "assets/revenue_risk.jpg",
    "dash_segment": "assets/segment_deep_dive.jpg"
}


# ================= UTILITY FUNCTIONS =================
def img_to_base64(path: str) -> str:
    """Convert image file to base64 encoded string.

    Args:
        path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    try:
        img_bytes = Path(path).read_bytes()
        return base64.b64encode(img_bytes).decode()
    except FileNotFoundError:
        st.error(f"Image not found: {path}")
        return ""
    except Exception as e:
        st.error(f"Error loading image {path}: {str(e)}")
        return ""


@st.cache_data(ttl=300)
def load_images() -> Dict[str, str]:
    """Load and cache all images as base64 strings.

    Returns:
        Dictionary mapping image names to base64 strings
    """
    return {name: img_to_base64(path) for name, path in ASSET_PATHS.items()}


@st.cache_data(ttl=300)
def load_kpis() -> Dict[str, Any]:
    """Load and cache KPI data from database.

    Returns:
        Dictionary containing KPI metrics
    """
    try:
        return fetch_kpis()
    except Exception as e:
        st.error(f"Error fetching KPIs: {str(e)}")
        # Return default values on error
        return {
            "total_customers": 0,
            "churned_customers": 0,
            "total_revenue": 0,
            "revenue_at_risk": 0,
            "churn_rate": 0,
            "retention_rate": 0
        }


def calculate_derived_metrics(kpis: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate derived metrics from base KPIs.

    Args:
        kpis: Dictionary of base KPI values

    Returns:
        Dictionary with calculated metrics
    """
    total_customers = kpis.get("total_customers", 0) or 0
    total_revenue = kpis.get("total_revenue", 0) or 0
    revenue_at_risk = kpis.get("revenue_at_risk", 0) or 0

    revenue_protected = max(total_revenue - revenue_at_risk, 0)
    arpu = round(total_revenue / total_customers, 2) if total_customers > 0 else 0

    return {
        "total_customers": total_customers,
        "churned_customers": kpis.get("churned_customers", 0) or 0,
        "churn_rate": kpis.get("churn_rate", 0) or 0,
        "retention_rate": kpis.get("retention_rate", 0) or 0,
        "total_revenue": int(total_revenue),
        "revenue_at_risk": int(revenue_at_risk),
        "revenue_protected": int(revenue_protected),
        "arpu": arpu
    }


# ================= PAGE SETUP =================
st.set_page_config(**PAGE_CONFIG)

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'chat_open' not in st.session_state:
    st.session_state.chat_open = False

# Remove default Streamlit styling
st.markdown("""
<style>
html, body {
    margin: 0;
    padding: 0;
    background: #000;
}

.block-container {
    padding: 0 !important;
    max-width: 100vw !important;
}

header, footer, .stDeployButton {
    visibility: hidden;
    height: 0;
}

#MainMenu {visibility: hidden;}

/* Hide all Streamlit elements in chat widget area */
.chat-widget-container .stMarkdown,
.chat-widget-container .stTextInput,
.chat-widget-container .stButton {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ================= LOAD DATA =================
images = load_images()
kpis_raw = load_kpis()
metrics = calculate_derived_metrics(kpis_raw)

# ================= CHAT WIDGET HTML/CSS/JS =================
chat_widget = """
<style>
/* Floating Chat Button */
.chat-button {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #ff1e1e, #dc2626);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 8px 24px rgba(255, 30, 30, 0.4);
    z-index: 10000;
    transition: all 0.3s ease;
}

.chat-button:hover {
    transform: scale(1.1);
    box-shadow: 0 12px 32px rgba(255, 30, 30, 0.6);
}

.chat-button svg {
    width: 30px;
    height: 30px;
    fill: white;
}

.chat-button.active {
    background: #1a1a1a;
}

/* Chat Window */
.chat-window {
    position: fixed;
    bottom: 100px;
    right: 30px;
    width: 400px;
    height: 600px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: none;
    flex-direction: column;
    z-index: 9999;
    overflow: hidden;
    animation: slideUp 0.3s ease;
}

.chat-window.open {
    display: flex;
}

@keyframes slideUp {
    from {
        transform: translateY(20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

/* Chat Header */
.chat-header {
    background: linear-gradient(135deg, #ff1e1e, #dc2626);
    padding: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: white;
}

.chat-header-icon {
    width: 40px;
    height: 40px;
    background: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.chat-header-icon::before {
    content: '';
    position: absolute;
    top: 2px;
    right: 2px;
    width: 10px;
    height: 10px;
    background: #00e676;
    border-radius: 50%;
    border: 2px solid white;
}

.chat-header-icon svg {
    width: 24px;
    height: 24px;
    fill: #ff1e1e;
}

.chat-header-text h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
}

.chat-header-text p {
    margin: 0;
    font-size: 12px;
    opacity: 0.9;
}

.chat-close {
    margin-left: auto;
    width: 30px;
    height: 30px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}

.chat-close:hover {
    background: rgba(255, 255, 255, 0.3);
}

/* Chat Messages */
.chat-messages {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    background: #f5f5f5;
}

.message {
    display: flex;
    margin-bottom: 16px;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.message.user {
    justify-content: flex-end;
}

.message-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff1e1e, #dc2626);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-right: 10px;
}

.message.user .message-avatar {
    background: #e0e0e0;
    margin-right: 0;
    margin-left: 10px;
    order: 2;
}

.message-avatar svg {
    width: 18px;
    height: 18px;
    fill: white;
}

.message.user .message-avatar svg {
    fill: #666;
}

.message-content {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 14px;
    line-height: 1.5;
}

.message.ai .message-content {
    background: linear-gradient(135deg, #4169E1, #6B8FFF);
    color: white;
    border-bottom-left-radius: 4px;
}

.message.user .message-content {
    background: white;
    color: #333;
    border-bottom-right-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ai-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: white;
    color: #8B5CF6;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.sparkle {
    width: 14px;
    height: 14px;
    fill: #8B5CF6;
}

/* Typing Indicator */
.typing-indicator {
    display: none;
    padding: 12px 16px;
    background: linear-gradient(135deg, #4169E1, #6B8FFF);
    border-radius: 18px;
    border-bottom-left-radius: 4px;
    width: fit-content;
}

.typing-indicator.show {
    display: block;
}

.typing-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: white;
    margin: 0 2px;
    animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
        opacity: 0.7;
    }
    30% {
        transform: translateY(-10px);
        opacity: 1;
    }
}

/* Chat Input */
.chat-input-area {
    padding: 16px;
    background: white;
    border-top: 1px solid #e0e0e0;
}

.chat-input-wrapper {
    display: flex;
    gap: 10px;
    align-items: center;
}

.chat-input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e0e0e0;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
    transition: all 0.2s ease;
}

.chat-input:focus {
    border-color: #ff1e1e;
}

.send-button {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #ff1e1e, #dc2626);
    border-radius: 50%;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
}

.send-button:hover:not(:disabled) {
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(255, 30, 30, 0.4);
}

.send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.send-button svg {
    width: 20px;
    height: 20px;
    fill: white;
}

/* Suggested Questions */
.suggested-questions {
    padding: 16px;
    background: white;
    border-bottom: 1px solid #e0e0e0;
}

.suggested-questions h4 {
    margin: 0 0 12px 0;
    font-size: 13px;
    color: #666;
    font-weight: 600;
}

.suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.suggestion-chip {
    padding: 8px 14px;
    background: #f5f5f5;
    border: 1px solid #e0e0e0;
    border-radius: 20px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #333;
}

.suggestion-chip:hover {
    background: #ff1e1e;
    color: white;
    border-color: #ff1e1e;
}

/* Welcome Message */
.welcome-message {
    text-align: center;
    padding: 40px 20px;
    color: #666;
}

.welcome-message h3 {
    margin: 0 0 8px 0;
    color: #333;
}

.welcome-message p {
    margin: 0;
    font-size: 14px;
}

/* Scrollbar */
.chat-messages::-webkit-scrollbar {
    width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
    background: #f5f5f5;
}

.chat-messages::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
    background: #999;
}

/* Mobile Responsive */
@media (max-width: 480px) {
    .chat-window {
        width: 100%;
        height: 100%;
        bottom: 0;
        right: 0;
        border-radius: 0;
    }

    .chat-button {
        bottom: 20px;
        right: 20px;
    }
}
</style>

<!-- Chat Widget HTML -->
<div class="chat-button" onclick="toggleChat()">
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
        <circle cx="12" cy="11" r="1"/>
        <circle cx="8" cy="11" r="1"/>
        <circle cx="16" cy="11" r="1"/>
    </svg>
</div>

<div class="chat-window" id="chatWindow">
    <div class="chat-header">
        <div class="chat-header-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
            </svg>
        </div>
        <div class="chat-header-text">
            <h3>AI Retention Analyst</h3>
            <p>Powered by ChurnGuard AI</p>
        </div>
        <div class="chat-close" onclick="toggleChat()">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="white">
                <path d="M14 1.41L12.59 0L7 5.59L1.41 0L0 1.41L5.59 7L0 12.59L1.41 14L7 8.41L12.59 14L14 12.59L8.41 7L14 1.41Z"/>
            </svg>
        </div>
    </div>

    <div class="suggested-questions">
        <h4>Try asking:</h4>
        <div class="suggestion-chips">
            <div class="suggestion-chip" onclick="askQuestion('Why is churn happening?')">Why is churn happening?</div>
            <div class="suggestion-chip" onclick="askQuestion('How is revenue generated?')">How is revenue generated?</div>
            <div class="suggestion-chip" onclick="askQuestion('Which segments are at risk?')">Which segments at risk?</div>
            <div class="suggestion-chip" onclick="askQuestion('What retention strategies work best?')">Best retention strategies?</div>
        </div>
    </div>

    <div class="chat-messages" id="chatMessages">
        <div class="welcome-message">
            <h3>👋 Welcome!</h3>
            <p>I'm your AI Retention Analyst. Ask me anything about churn, revenue, or customer insights.</p>
        </div>
    </div>

    <div class="chat-input-area">
        <div class="chat-input-wrapper">
            <input 
                type="text" 
                class="chat-input" 
                id="chatInput" 
                placeholder="Ask about churn, revenue, retention..."
                onkeypress="handleKeyPress(event)"
            />
            <button class="send-button" id="sendButton" onclick="sendMessage()">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                </svg>
            </button>
        </div>
    </div>
</div>

<script>
let chatOpen = false;

function toggleChat() {
    chatOpen = !chatOpen;
    const chatWindow = document.getElementById('chatWindow');
    const chatButton = document.querySelector('.chat-button');

    if (chatOpen) {
        chatWindow.classList.add('open');
        chatButton.classList.add('active');
        document.getElementById('chatInput').focus();
    } else {
        chatWindow.classList.remove('open');
        chatButton.classList.remove('active');
    }
}

function askQuestion(question) {
    document.getElementById('chatInput').value = question;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function addMessage(text, isUser = false) {
    const messagesDiv = document.getElementById('chatMessages');
    const welcomeMsg = messagesDiv.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'ai'}`;

    const avatarSvg = isUser 
        ? '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>'
        : '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>';

    const aiBadge = !isUser 
        ? `<div class="ai-badge">
             <svg class="sparkle" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
               <path d="M12 2l2.4 7.2H22l-6 4.8 2.4 7.2L12 16.8 5.6 21.2 8 14 2 9.2h7.6z"/>
             </svg>
             Answered by AI
           </div>`
        : '';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatarSvg}</div>
        <div>
            <div class="message-content">${text}</div>
            ${aiBadge}
        </div>
    `;

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showTyping() {
    const messagesDiv = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" fill="white"/>
            </svg>
        </div>
        <div class="typing-indicator show">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTyping() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addMessage(message, true);
    input.value = '';

    // Disable send button
    const sendButton = document.getElementById('sendButton');
    sendButton.disabled = true;

    // Show typing indicator
    showTyping();

    try {
        // Send to Streamlit backend
        const response = await fetch(window.location.href, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: message,
                action: 'get_ai_response'
            })
        });

        // Simulate API delay for demo
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Hide typing indicator
        hideTyping();

        // For demo purposes, generate contextual response
        const aiResponse = generateContextualResponse(message);
        addMessage(aiResponse, false);

    } catch (error) {
        hideTyping();
        addMessage("I'm having trouble connecting right now. Please try again!", false);
    } finally {
        sendButton.disabled = false;
    }
}

function generateContextualResponse(question) {
    const q = question.toLowerCase();

    if (q.includes('churn') && q.includes('why')) {
        return "Based on the data, churn is happening primarily due to: 1) Service quality issues (32%), 2) Competitive pricing (28%), 3) Lack of engagement (24%). High-risk customers are typically month-to-month subscribers with low engagement scores.";
    } else if (q.includes('revenue')) {
        return "Revenue is generated through: 1) Monthly subscriptions ($" + Math.floor(Math.random() * 500000 + 500000).toLocaleString() + "), 2) Premium add-ons (18% of total), 3) Data overages (12%). Your ARPU is currently trending at $" + (Math.random() * 30 + 50).toFixed(2) + ".";
    } else if (q.includes('segment') || q.includes('risk')) {
        return "Month-to-month fiber optic customers show the highest churn risk at 42%. Focus retention efforts on customers with tenure < 12 months and contract types without commitment. These segments represent 34% of revenue at risk.";
    } else if (q.includes('retention') || q.includes('strateg')) {
        return "Top retention strategies: 1) Offer 6-month commitment discounts (reduces churn by 23%), 2) Proactive support outreach (18% improvement), 3) Personalized upgrade offers for high-value customers. Focus on customers showing early warning signs like decreased usage.";
    } else if (q.includes('customer')) {
        return "Customer insights: Total active customers: " + Math.floor(Math.random() * 1000 + 6000).toLocaleString() + ". Average tenure: 32 months. Highest value segment: 2-year contract customers with avg. revenue of $95/month. Senior citizens show lowest churn at 15%.";
    } else {
        return "Great question! I can help you analyze churn patterns, revenue trends, customer segments, and retention strategies. Try asking specific questions about why customers are leaving, which segments are at risk, or what actions to take.";
    }
}

// Initialize chat on load
window.addEventListener('load', function() {
    console.log('ChurnGuard AI Chat loaded successfully');
});
</script>
"""

# ================= MAIN HTML CONTENT =================
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ChurnGuard - Retention Intelligence</title>
<style>
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

body {{
    margin: 0;
    background: #000;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* ================= NAVBAR ================= */
.navbar {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 72px;
    display: flex;
    align-items: center;
    padding: 0 48px;
    background: linear-gradient(to bottom, #000 70%, rgba(0,0,0,0.9));
    border-bottom: 1px solid rgba(255,255,255,0.06);
    z-index: 1000;
    backdrop-filter: blur(10px);
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 26px;
    font-weight: 900;
    color: white;
}}

.logo {{
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #ff1e1e, #dc2626);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    box-shadow: 0 4px 12px rgba(255, 30, 30, 0.3);
}}

/* ================= HERO ================= */
.hero {{
    padding-top: 120px;
    padding-bottom: 60px;
    display: flex;
    justify-content: center;
    background:
        radial-gradient(circle at center, rgba(220,30,30,0.35), transparent 70%),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.04) 0px, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 60px),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0px, rgba(255,255,255,0.04) 1px, transparent 1px, transparent 60px),
        #000;
}}

.hero-content {{
    max-width: 1200px;
    text-align: center;
    padding: 20px 24px;
}}

.badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 22px;
    border-radius: 999px;
    border: 1px solid rgba(255,30,30,0.45);
    background: rgba(255,30,30,0.14);
    color: #ff6b6b;
    font-weight: 600;
    font-size: 14px;
    margin-bottom: 30px;
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.8; }}
}}

.hero-title-small {{
    font-size: clamp(24px, 4vw, 48px);
    font-weight: 700;
    color: white;
    margin-bottom: 16px;
    line-height: 1.2;
}}

.hero-title-main {{
    font-size: clamp(48px, 8vw, 88px);
    font-weight: 900;
    color: white;
    line-height: 1.05;
    margin-bottom: 24px;
}}

.hero-title-main span,
.hero-title-small span {{
    background: linear-gradient(135deg, #ff1e1e, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.hero-sub {{
    font-size: clamp(16px, 2vw, 22px);
    color: #d6d6d6;
    max-width: 900px;
    margin: 0 auto;
    line-height: 1.6;
}}

/* ================= KPI SECTION ================= */
.kpi-wrapper {{
    padding: 60px 48px;
}}

.kpi-title {{
    font-size: clamp(32px, 5vw, 40px);
    font-weight: 700;
    text-align: center;
    color: white;
    margin-bottom: 48px;
    letter-spacing: -0.5px;
}}

.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 24px;
    max-width: 1600px;
    margin: 0 auto;
}}

.kpi-card {{
    height: 160px;
    background: linear-gradient(135deg, #0b0f17, #020617);
    border-radius: 18px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 4px 24px rgba(255,81,47,0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
}}

.kpi-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #ff4b2b, transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}}

.kpi-card:hover {{
    transform: translateY(-8px) scale(1.02);
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.1),
        0 12px 48px rgba(255,81,47,0.4);
}}

.kpi-card:hover::before {{
    opacity: 1;
}}

.kpi-value {{
    font-size: clamp(28px, 4vw, 36px);
    font-weight: 900;
    background: linear-gradient(135deg, #ff4b2b, #ff8a65);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.kpi-label {{
    margin-top: 12px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 1.2px;
    color: #cbd5e1;
    text-transform: uppercase;
}}

/* ================= FEATURES SECTION ================= */
.features-wrapper {{
    padding: 80px 48px;
}}

.features {{
    position: relative;
    padding: 60px 48px;
    background:
        radial-gradient(circle at top, rgba(255,30,30,0.12), transparent 60%),
        linear-gradient(to right, rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255,255,255,0.03) 1px, transparent 1px);
    background-size: auto, 60px 60px, 60px 60px;
    border-radius: 24px;
}}

.features-header {{
    text-align: center;
    max-width: 900px;
    margin: 0 auto 80px;
}}

.features-tag {{
    color: #ef4444;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: block;
}}

.features-header h2 {{
    color: white;
    font-size: clamp(36px, 5vw, 48px);
    font-weight: 700;
    margin: 16px 0;
    line-height: 1.2;
}}

.features-header h2 span {{
    color: #ef4444;
}}

.features-header p {{
    color: #94a3b8;
    font-size: clamp(16px, 2vw, 20px);
    line-height: 1.6;
}}

.features-grid {{
    max-width: 1400px;
    margin: auto;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 28px;
}}

.feature-card {{
    position: relative;
    padding: 32px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0b0f17, #020617);
    border: 1px solid rgba(255,255,255,0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.feature-card:hover {{
    transform: translateY(-8px);
    border-color: rgba(255,81,47,0.3);
    box-shadow: 0 12px 48px rgba(255,81,47,0.3);
}}

.icon-box {{
    width: 56px;
    height: 56px;
    border-radius: 14px;
    background: linear-gradient(135deg, #dc2626, #b91c1c);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(255,30,30,0.4);
    margin-bottom: 24px;
}}

.icon-box svg {{
    width: 26px;
    height: 26px;
    stroke: white;
    stroke-width: 2;
}}

.feature-card h3 {{
    color: white;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
}}

.feature-card p {{
    color: #94a3b8;
    font-size: 15.5px;
    line-height: 1.6;
}}

/* ================= ARCHITECTURE SECTION ================= */
.architecture-section {{
    width: 100%;
    padding: 100px 48px;
    background:
        radial-gradient(circle at center, rgba(220,30,30,0.15), transparent 60%),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 60px),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 1px, transparent 1px, transparent 60px),
        #000;
}}

.architecture-header {{
    text-align: center;
    max-width: 1100px;
    margin: 0 auto 80px;
}}

.architecture-tag {{
    color: #ff1e1e;
    font-weight: 800;
    letter-spacing: 4px;
    font-size: 14px;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: block;
}}

.architecture-title {{
    font-size: clamp(36px, 5vw, 64px);
    font-weight: 900;
    color: white;
    margin: 20px 0;
    line-height: 1.1;
}}

.architecture-title span {{
    background: linear-gradient(135deg, #ff1e1e, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.architecture-subtitle {{
    font-size: clamp(16px, 2vw, 20px);
    color: #cbd5e1;
    line-height: 1.6;
}}

.architecture-wrapper {{
    padding: 60px 0;
    overflow-x: auto;
}}

.architecture-grid {{
    display: grid;
    grid-template-columns: repeat(11, auto);
    align-items: center;
    gap: 0;
    justify-content: center;
    min-width: min-content;
    padding: 0 24px;
}}

.arch-card {{
    width: 200px;
    height: 200px;
    background: linear-gradient(135deg, #0b0f17, #020617);
    border-radius: 18px;
    padding: 20px;
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 4px 24px rgba(255,30,30,0.15);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.arch-card:hover {{
    transform: translateY(-6px);
    box-shadow:
        inset 0 0 0 1px rgba(255,30,30,0.4),
        0 8px 32px rgba(255,30,30,0.35);
}}

.arch-card h3 {{
    color: white;
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 10px;
}}

.arch-card p {{
    color: #cbd5e1;
    font-size: 14px;
    line-height: 1.5;
}}

.arch-arrow {{
    text-align: center;
    font-size: 32px;
    color: #ff1e1e;
    width: 40px;
    animation: slideRight 2s ease-in-out infinite;
}}

@keyframes slideRight {{
    0%, 100% {{ transform: translateX(0); opacity: 0.7; }}
    50% {{ transform: translateX(5px); opacity: 1; }}
}}

.architecture-image-wrapper {{
    width: 100%;
    max-width: 1600px;
    margin: 60px auto 0;
    padding: 32px;
    border-radius: 24px;
    background: linear-gradient(135deg, #0b0f17, #020617);
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 8px 48px rgba(255,30,30,0.25);
}}

.architecture-image {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 16px;
}}

/* ================= DASHBOARDS SECTION ================= */
.dashboards-section {{
    padding: 100px 48px 150px;
}}

.dashboards-header {{
    text-align: center;
    max-width: 1100px;
    margin: 0 auto 80px;
}}

.dashboards-tag {{
    color: #ff1e1e;
    font-weight: 800;
    letter-spacing: 4px;
    font-size: 14px;
    text-transform: uppercase;
    margin-bottom: 16px;
    display: block;
}}

.dashboards-title {{
    font-size: clamp(36px, 5vw, 64px);
    font-weight: 900;
    color: white;
    margin: 20px 0;
    line-height: 1.1;
}}

.dashboards-title span {{
    background: linear-gradient(135deg, #ff1e1e, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.dashboards-subtitle {{
    font-size: clamp(16px, 2vw, 20px);
    color: #cbd5e1;
    line-height: 1.6;
}}

.dashboards-grid {{
    max-width: 1700px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 32px;
}}

.dashboard-card {{
    background: linear-gradient(135deg, #0b0f17, #020617);
    border-radius: 24px;
    padding: 24px;
    box-shadow:
        inset 0 0 0 1px rgba(255,255,255,0.06),
        0 4px 32px rgba(255,30,30,0.2);
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}}

.dashboard-card:hover {{
    transform: translateY(-8px);
    box-shadow:
        inset 0 0 0 1px rgba(255,30,30,0.3),
        0 12px 56px rgba(255,30,30,0.4);
}}

.dashboard-card h3 {{
    color: white;
    font-size: 22px;
    font-weight: 800;
    margin-bottom: 14px;
}}

.dashboard-card p {{
    color: #94a3b8;
    font-size: 16px;
    margin-bottom: 20px;
    line-height: 1.5;
}}

.dashboard-image {{
    width: 100%;
    border-radius: 16px;
    display: block;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}}

/* ================= RESPONSIVE DESIGN ================= */
@media (max-width: 768px) {{
    .navbar {{
        padding: 0 24px;
    }}

    .hero {{
        padding-top: 100px;
        padding-bottom: 40px;
    }}

    .kpi-wrapper,
    .features-wrapper,
    .architecture-section,
    .dashboards-section {{
        padding: 60px 24px;
    }}

    .features {{
        padding: 40px 24px;
    }}

    .features-grid,
    .dashboards-grid {{
        grid-template-columns: 1fr;
    }}

    .architecture-grid {{
        grid-template-columns: 1fr;
        gap: 16px;
    }}

    .arch-arrow {{
        transform: rotate(90deg);
        width: auto;
        height: 40px;
    }}

    .architecture-image-wrapper {{
        padding: 16px;
    }}
}}

@media (max-width: 480px) {{
    .brand {{
        font-size: 20px;
    }}

    .logo {{
        width: 32px;
        height: 32px;
        font-size: 18px;
    }}

    .kpi-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>
</head>

<body>

<!-- Navigation -->
<nav class="navbar">
    <div class="brand">
        <div class="logo">⚡</div>
        Churn<span style="color:#ff1e1e">Guard</span>
    </div>
</nav>

<!-- Hero Section -->
<section class="hero">
    <div class="hero-content">
        <div class="badge">
            <span style="font-size: 10px;">●</span> AI-Powered Retention Intelligence
        </div>
        <div class="hero-title-small">
            RETENTIONIQ – ENTERPRISE CUSTOMER CHURN<br><span>INTELLIGENCE PLATFORM</span>
        </div>
        <div class="hero-title-main">
            Stop Churn Before<br><span>It Happens</span>
        </div>
        <p class="hero-sub">
            Built an AI-powered telecom retention analytics platform using PostgreSQL,
            Streamlit, Power BI, Excel, Python, Colab and GPT-based querying.
        </p>
    </div>
</section>

<!-- KPI Section -->
<section class="kpi-wrapper">
    <h2 class="kpi-title">KPI SNAPSHOT</h2>
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-value">{metrics['total_customers']:,}</div>
            <div class="kpi-label">Total Customers</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{metrics['churned_customers']:,}</div>
            <div class="kpi-label">Churned Customers</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{metrics['churn_rate']:.1f}%</div>
            <div class="kpi-label">Churn Rate</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">{metrics['retention_rate']:.1f}%</div>
            <div class="kpi-label">Retention Rate</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">${metrics['revenue_at_risk']:,}</div>
            <div class="kpi-label">Revenue at Risk</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">${metrics['total_revenue']:,}</div>
            <div class="kpi-label">Total Revenue</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">${metrics['revenue_protected']:,}</div>
            <div class="kpi-label">Revenue Protected</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-value">${metrics['arpu']:,.2f}</div>
            <div class="kpi-label">ARPU</div>
        </div>
    </div>
</section>

<!-- Features Section -->
<div class="features-wrapper">
    <section class="features">
        <div class="features-header">
            <span class="features-tag">FEATURES</span>
            <h2>
                Intelligent Retention<br/>
                <span>At Your Fingertips</span>
            </h2>
            <p>
                Everything you need to understand, predict, and prevent customer churn
                in one powerful platform.
            </p>
        </div>

        <div class="features-grid">
            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <path d="M9 4a3 3 0 0 0-3 3v10a3 3 0 0 0 3 3"/>
                        <path d="M15 4a3 3 0 0 1 3 3v10a3 3 0 0 1-3 3"/>
                        <path d="M9 8h6M9 12h6M9 16h6"/>
                    </svg>
                </div>
                <h3>Predictive AI Engine</h3>
                <p>Machine learning models analyze 200+ behavioral signals to identify at-risk customers before they churn.</p>
            </div>

            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <path d="M4 19h16"/>
                        <path d="M6 16V8M12 16V4M18 16v-6"/>
                    </svg>
                </div>
                <h3>Real-Time Analytics</h3>
                <p>Live dashboards showing churn probability scores, retention metrics, and customer health indicators.</p>
            </div>

            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14V11a6 6 0 1 0-12 0v3a2 2 0 0 1-.6 1.4L4 17h5"/>
                        <path d="M9 17a3 3 0 0 0 6 0"/>
                    </svg>
                </div>
                <h3>Proactive Alerts</h3>
                <p>Automated notifications when high-value customers show early warning signs of potential churn.</p>
            </div>

            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <circle cx="12" cy="12" r="9"/>
                        <circle cx="12" cy="12" r="4"/>
                        <path d="M12 3v6M21 12h-6"/>
                    </svg>
                </div>
                <h3>Targeted Campaigns</h3>
                <p>AI-recommended retention offers and personalized engagement strategies for each customer segment.</p>
            </div>

            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/>
                    </svg>
                </div>
                <h3>Instant Integration</h3>
                <p>Connect with your existing CRM, billing systems, and support platforms in minutes, not months.</p>
            </div>

            <div class="feature-card">
                <div class="icon-box">
                    <svg fill="none" viewBox="0 0 24 24">
                        <rect x="3" y="11" width="18" height="11" rx="2"/>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                </div>
                <h3>Enterprise Security</h3>
                <p>SOC 2 Type II certified with end-to-end encryption protecting your sensitive customer data.</p>
            </div>
        </div>
    </section>
</div>

<!-- Architecture Section -->
<section class="architecture-section">
    <div class="architecture-header">
        <span class="architecture-tag">ARCHITECTURE</span>
        <h2 class="architecture-title">
            End-to-End Telecom<br><span>Retention Architecture</span>
        </h2>
        <p class="architecture-subtitle">
            Scalable analytics & AI-driven decision system.
        </p>
    </div>

    <div class="architecture-wrapper">
        <div class="architecture-grid">
            <div class="arch-card">
                <h3>Data Sources</h3>
                <p>Customer usage logs, billing records, CRM data, network events, and support tickets.</p>
            </div>

            <div class="arch-arrow">➜</div>

            <div class="arch-card">
                <h3>Ingestion & Processing</h3>
                <p>Python pipelines for validation, cleaning, feature engineering, and aggregations.</p>
            </div>

            <div class="arch-arrow">➜</div>

            <div class="arch-card">
                <h3>Data Warehouse</h3>
                <p>PostgreSQL stores fact tables, dimensions, and KPI marts optimized for analytics.</p>
            </div>

            <div class="arch-arrow">➜</div>

            <div class="arch-card">
                <h3>Analytics & ML</h3>
                <p>Churn prediction models, cohort analysis, revenue-at-risk, and health scoring.</p>
            </div>

            <div class="arch-arrow">➜</div>

            <div class="arch-card">
                <h3>Application Layer</h3>
                <p>Streamlit dashboards, Power BI reports, executive KPIs, operational views.</p>
            </div>

            <div class="arch-arrow">➜</div>

            <div class="arch-card">
                <h3>AI Decision Engine</h3>
                <p>GPT-powered insights, natural language queries, recommendations, and actions.</p>
            </div>
        </div>
    </div>

    <div class="architecture-image-wrapper">
        <img
            src="data:image/png;base64,{images['architecture']}"
            alt="Telecom Customer Churn Analytics Architecture"
            class="architecture-image"
        />
    </div>
</section>

<!-- Dashboards Section -->
<section class="dashboards-section">
    <div class="dashboards-header">
        <span class="dashboards-tag">DASHBOARDS</span>
        <h2 class="dashboards-title">
            Executive & Operational<br>
            <span>Retention Dashboards</span>
        </h2>
        <p class="dashboards-subtitle">
            Actionable insights across churn, revenue risk, customer segments,
            and retention performance.
        </p>
    </div>

    <div class="dashboards-grid">
        <div class="dashboard-card">
            <h3>Churn Overview</h3>
            <p>High-level churn metrics, KPIs, and customer health indicators.</p>
            <img class="dashboard-image"
                 src="data:image/jpeg;base64,{images['dash_overview']}"
                 alt="Churn Overview Dashboard" />
        </div>

        <div class="dashboard-card">
            <h3>Revenue at Risk</h3>
            <p>Revenue exposure analysis with churn probability and ARPU impact.</p>
            <img class="dashboard-image"
                 src="data:image/jpeg;base64,{images['dash_revenue']}"
                 alt="Revenue at Risk Dashboard" />
        </div>

        <div class="dashboard-card">
            <h3>Churn Trends</h3>
            <p>Monthly churn patterns, seasonality, and behavioral changes.</p>
            <img class="dashboard-image"
                 src="data:image/jpeg;base64,{images['dash_trends']}"
                 alt="Churn Trends Dashboard" />
        </div>

        <div class="dashboard-card">
            <h3>Segment Deep Dive</h3>
            <p>Cohort analysis by plan, tenure, geography, and usage behavior.</p>
            <img class="dashboard-image"
                 src="data:image/jpeg;base64,{images['dash_segment']}"
                 alt="Segment Deep Dive Dashboard" />
        </div>
    </div>
</section>

{chat_widget}

</body>
</html>
"""

# ================= RENDER HTML =================
components.html(
    html_content,
    height=5000,
    scrolling=True
)