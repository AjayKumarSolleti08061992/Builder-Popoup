/**
 * The Café Companion — Conversational Barista Script (Aura)
 * Powers natural language ordering, multi-turn dialogue, dietary customization,
 * and direct one-click shopping cart integration via Google Gemini AI.
 */

const chatState = {
  history: [], // [{ role: 'user' | 'model', content: '...' }]
  isAwaitingReply: false,
};

function sendQuickPrompt(promptText) {
  const input = document.getElementById('chatInput');
  input.value = promptText;
  handleChatSubmit(new Event('submit'));
}

async function handleChatSubmit(event) {
  if (event) event.preventDefault();
  const input = document.getElementById('chatInput');
  const userText = input.value.trim();
  if (!userText || chatState.isAwaitingReply) return;

  // Append user message to UI and history
  appendChatMessage('user', userText);
  chatState.history.push({ role: 'user', content: userText });
  input.value = '';

  // Show Aura typing indicator
  const typingEl = appendTypingIndicator();
  chatState.isAwaitingReply = true;

  try {
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userText,
        history: chatState.history,
      }),
    });

    const data = await res.json();
    typingEl.remove();

    if (data.status === 'success') {
      const reply = data.reply || "I'd love to craft that specialty cup for you!";
      chatState.history.push({ role: 'model', content: reply });
      appendChatMessage('model', reply, data.suggested_items);
    } else {
      appendChatMessage('model', "I had a brief glitch connecting to my coffee notes. What can I brew for you?");
    }
  } catch (err) {
    console.error('Chat error:', err);
    if (typingEl) typingEl.remove();
    appendChatMessage('model', "I'm having a brief connection pause. Feel free to browse our menu catalog directly!");
  } finally {
    chatState.isAwaitingReply = false;
  }
}

function appendChatMessage(role, text, suggestedItems = []) {
  const container = document.getElementById('chatMessagesContainer');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${role}`;

  // Basic markdown bold parsing
  const formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Build suggested items buttons if present
  let suggestionsHtml = '';
  if (suggestedItems && suggestedItems.length > 0) {
    suggestionsHtml = suggestedItems.map((item) => `
      <div>
        <button type="button" class="chat-suggested-item-btn" onclick="addSuggestedItemByName('${item.name.replace(/'/g, "\\'")}', '${(item.notes || '').replace(/'/g, "\\'")}')">
          🛒 + Add "${item.name}" to Order
        </button>
      </div>
    `).join('');
  }

  msgDiv.innerHTML = `
    <div class="message-bubble">
      <p>${formattedText}</p>
      ${suggestionsHtml}
    </div>
    <span class="message-time">Just now</span>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
  const container = document.getElementById('chatMessagesContainer');
  const typingDiv = document.createElement('div');
  typingDiv.className = 'chat-message model';
  typingDiv.id = 'chatTypingIndicator';
  typingDiv.innerHTML = `
    <div class="message-bubble" style="padding: 0.6rem 1rem;">
      <span style="font-size: 0.8rem; color: var(--text-muted); font-style: italic;">
        ✨ Aura is brewing a personalized reply...
      </span>
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
  return typingDiv;
}

function addSuggestedItemByName(itemName, notes) {
  if (window.state && window.state.menuItems) {
    const matched = window.state.menuItems.find(
      (i) => i.name.toLowerCase() === itemName.toLowerCase()
    );
    if (matched) {
      window.addItemToCart(matched.id, notes);
      return;
    }
  }
  // Fallback to first item if not found by exact string
  if (window.addItemToCart) {
    window.addItemToCart(1, notes);
  }
}

function resetChatHistory() {
  chatState.history = [];
  const container = document.getElementById('chatMessagesContainer');
  if (container) {
    container.innerHTML = `
      <div class="chat-message model">
        <div class="message-bubble">
          <p>Welcome to <strong>The Artisan Roast &amp; Byte</strong>! ☕ I'm Aura, your AI café companion.</p>
          <p>Tell me what you're in the mood for, your dietary preferences, or ask for a personalized recommendation for your workday!</p>
        </div>
        <span class="message-time">Just now</span>
      </div>
    `;
  }
}

// Attach globally
window.handleChatSubmit = handleChatSubmit;
window.sendQuickPrompt = sendQuickPrompt;
window.resetChatHistory = resetChatHistory;
window.addSuggestedItemByName = addSuggestedItemByName;
