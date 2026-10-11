/**
 * The Café Companion — Core Application Script
 * Manages UI state, menu catalog, shopping cart, live order pipeline,
 * flavor discovery, communal lounge, and table feedback.
 */

// Application Global State
const state = {
  activeView: 'customer', // 'customer' or 'barista'
  menuItems: [],
  activeCategory: 'All',
  cart: [],
  currentOrder: null,
  activePatrons: [],
  starRating: 5,
  liveWaitInterval: null,
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  await fetchMenu();
  await fetchCommunalPatrons();
  await fetchRoomTelemetry();
  checkExistingOrderSession();
  setupSmoothScrolling();
}

/**
 * Perspective Switcher: Toggle between Customer Lounge & Barista Kitchen
 */
function switchView(viewName) {
  state.activeView = viewName;
  const customerView = document.getElementById('customerView');
  const baristaView = document.getElementById('baristaView');
  const btnCustomer = document.getElementById('viewCustomerBtn');
  const btnBarista = document.getElementById('viewBaristaBtn');

  if (viewName === 'customer') {
    customerView.style.display = 'block';
    baristaView.style.display = 'none';
    btnCustomer.classList.add('active');
    btnBarista.classList.remove('active');
  } else {
    customerView.style.display = 'none';
    baristaView.style.display = 'block';
    btnCustomer.classList.remove('active');
    btnBarista.classList.add('active');
    if (window.refreshBaristaDashboard) {
      window.refreshBaristaDashboard();
    }
  }
}

/**
 * Fetch and Render Menu Catalog
 */
async function fetchMenu() {
  try {
    const res = await fetch('/api/menu');
    const data = await res.json();
    if (data.status === 'success') {
      state.menuItems = data.items;
      renderMenu();
    }
  } catch (err) {
    console.error('Failed to load menu catalog:', err);
  }
}

function filterMenuCategory(category) {
  state.activeCategory = category;
  document.querySelectorAll('.menu-tab').forEach((tab) => {
    tab.classList.toggle('active', tab.textContent.trim() === category || (category === 'All' && tab.textContent.trim() === 'All Items'));
  });
  renderMenu();
}

function renderMenu() {
  const grid = document.getElementById('menuItemsGrid');
  if (!grid) return;

  const filtered = state.activeCategory === 'All'
    ? state.menuItems
    : state.menuItems.filter((item) => item.category === state.activeCategory);

  if (filtered.length === 0) {
    grid.innerHTML = '<div class="empty-sub">No items found in this category.</div>';
    return;
  }

  grid.innerHTML = filtered.map((item) => {
    const tagsHtml = item.tags.map(t => `<span class="tag-badge">${t}</span>`).join('');
    const imageSrc = item.image_url || '/static/images/artisan_latte.jpg';

    return `
      <div class="menu-item-card" data-item-id="${item.id}">
        <div class="menu-item-img-wrapper">
          <img src="${imageSrc}" alt="${item.name}" class="menu-item-img" loading="lazy">
          <span class="item-price-tag">$${item.price.toFixed(2)}</span>
        </div>
        <div class="menu-item-info">
          <h4 class="menu-item-name">${item.name}</h4>
          <p class="menu-item-desc">${item.description}</p>
          <div class="menu-item-tags-row">${tagsHtml}</div>
          <button type="button" class="btn-add-to-cart" onclick="addItemToCart(${item.id})">
            + Add to Order
          </button>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Shopping Cart Management
 */
function toggleCartDrawer() {
  const overlay = document.getElementById('cartOverlay');
  overlay.classList.toggle('open');
}

function closeCartDrawer(event) {
  const overlay = document.getElementById('cartOverlay');
  overlay.classList.remove('open');
}

function addItemToCart(itemId, customNotes = '') {
  const item = state.menuItems.find((i) => i.id === itemId);
  if (!item) return;

  const existing = state.cart.find((c) => c.id === item.id);
  if (existing) {
    existing.quantity += 1;
  } else {
    state.cart.push({
      id: item.id,
      name: item.name,
      price: item.price,
      quantity: 1,
      notes: customNotes,
    });
  }

  updateCartUI();
  // Open cart drawer briefly or flash badge
  const badge = document.getElementById('cartCountBadge');
  badge.classList.add('pulse');
  setTimeout(() => badge.classList.remove('pulse'), 400);
}

function updateCartQty(itemId, delta) {
  const index = state.cart.findIndex((c) => c.id === itemId);
  if (index === -1) return;

  state.cart[index].quantity += delta;
  if (state.cart[index].quantity <= 0) {
    state.cart.splice(index, 1);
  }

  updateCartUI();
}

function updateCartUI() {
  const list = document.getElementById('cartItemsList');
  const countBadge = document.getElementById('cartCountBadge');
  const totalPriceEl = document.getElementById('cartTotalPrice');
  const waitEstimateEl = document.getElementById('cartWaitEstimate');

  const totalQty = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  countBadge.textContent = totalQty;
  totalPriceEl.textContent = `$${totalPrice.toFixed(2)}`;

  // Approximate wait based on cart item count
  const estimatedWait = Math.max(3, Math.round(3 + (totalQty * 1.5)));
  waitEstimateEl.textContent = `~${estimatedWait} mins`;

  if (state.cart.length === 0) {
    list.innerHTML = `
      <div class="empty-cart-state" id="emptyCartState">
        <span class="empty-cart-icon">☕</span>
        <p>Your order is currently empty.</p>
        <p class="empty-sub">Ask Aura in chat or browse the menu to add delicious items!</p>
      </div>
    `;
    return;
  }

  list.innerHTML = state.cart.map((item) => `
    <div class="cart-item-row">
      <div class="cart-item-info">
        <h5>${item.name}</h5>
        <span>$${(item.price * item.quantity).toFixed(2)}</span>
      </div>
      <div class="cart-qty-controls">
        <button type="button" class="qty-btn" onclick="updateCartQty(${item.id}, -1)">−</button>
        <span>${item.quantity}</span>
        <button type="button" class="qty-btn" onclick="updateCartQty(${item.id}, 1)">+</button>
      </div>
    </div>
  `).join('');
}

/**
 * Submit Order & Initiate Better Waits Pipeline
 */
async function submitCartOrder() {
  if (state.cart.length === 0) {
    alert('Please add at least one item to your order first!');
    return;
  }

  const nameInput = document.getElementById('cartCustomerName');
  const tableInput = document.getElementById('cartTableNumber');
  const notesInput = document.getElementById('cartSpecialNotes');

  const customerName = nameInput.value.trim() || 'Café Guest';
  const tableNumber = tableInput.value.trim() || 'Table 4 (Window Bar)';
  const specialNotes = notesInput.value.trim();

  const payload = {
    customer_name: customerName,
    table_number: tableNumber,
    items: state.cart.map((i) => ({
      id: i.id,
      name: i.name,
      price: i.price,
      quantity: i.quantity,
    })),
    special_notes: specialNotes,
  };

  try {
    const btn = document.getElementById('btnPlaceOrder');
    btn.disabled = true;
    btn.innerHTML = '<span>Transmitting Ticket to Barista...</span>';

    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (data.status === 'success') {
      state.currentOrder = data.order;
      sessionStorage.setItem('current_cafe_order', JSON.stringify(data.order));
      
      // Clear cart
      state.cart = [];
      updateCartUI();
      toggleCartDrawer();

      // Update Pipeline UI
      activateOrderPipeline(data.order);

      // Scroll to Waits section
      document.getElementById('waitsSection').scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    console.error('Order creation failed:', err);
    alert('Could not submit order. Please try again.');
  } finally {
    const btn = document.getElementById('btnPlaceOrder');
    btn.disabled = false;
    btn.innerHTML = '<span>Place Order with Live Tracking</span>';
  }
}

/**
 * Better Waits Pipeline Tracker
 */
function activateOrderPipeline(order) {
  const badge = document.getElementById('activeOrderBadge');
  const subtitle = document.getElementById('activeOrderSubtitle');
  const waitMinDisplay = document.getElementById('dynamicWaitMinutes');
  const progressBar = document.getElementById('orderProgressBar');
  const notesDetail = document.getElementById('waitNotesDetail');

  badge.textContent = `Order #${order.order_code}`;
  subtitle.textContent = `Prepared for ${order.customer_name} at ${order.table_number}. Tracking live brewing status:`;
  waitMinDisplay.textContent = `~${order.estimated_wait_minutes}`;
  progressBar.style.width = '25%';

  // Update Telemetry Bar
  const telemetryWait = document.getElementById('currentWaitTimeDisplay');
  if (telemetryWait) telemetryWait.textContent = `~${order.estimated_wait_minutes} mins`;

  updatePipelineStage(order.status || 'placed');

  // Start simulated realistic preparation progression
  if (state.liveWaitInterval) clearInterval(state.liveWaitInterval);
  simulateLiveBrewingProgression(order);
}

function updatePipelineStage(stage) {
  const steps = ['placed', 'brewing', 'artistry', 'ready'];
  const stageMap = {
    'placed': 0,
    'brewing': 1,
    'artistry': 2,
    'ready': 3,
    'served': 3,
  };

  const activeIndex = stageMap[stage] ?? 0;

  steps.forEach((s, idx) => {
    const el = document.getElementById(`step-${s}`);
    if (!el) return;
    if (idx < activeIndex) {
      el.className = 'stepper-step completed';
    } else if (idx === activeIndex) {
      el.className = 'stepper-step active';
    } else {
      el.className = 'stepper-step';
    }
  });

  // Lines
  for (let i = 1; i <= 3; i++) {
    const line = document.getElementById(`line-${i}`);
    if (line) {
      line.classList.toggle('active', i <= activeIndex);
    }
  }

  const progressBar = document.getElementById('orderProgressBar');
  if (progressBar) {
    const pcts = [25, 55, 80, 100];
    progressBar.style.width = `${pcts[activeIndex] || 25}%`;
  }
}

function simulateLiveBrewingProgression(order) {
  let currentStageIdx = 0;
  const stages = ['placed', 'brewing', 'artistry', 'ready'];
  const notesDetail = document.getElementById('waitNotesDetail');
  const waitMinDisplay = document.getElementById('dynamicWaitMinutes');

  state.liveWaitInterval = setInterval(() => {
    currentStageIdx += 1;
    if (currentStageIdx >= stages.length) {
      clearInterval(state.liveWaitInterval);
      updatePipelineStage('ready');
      waitMinDisplay.textContent = 'READY!';
      notesDetail.innerHTML = '<strong>✨ Pick up at Main Bar!</strong> Your handcrafted specialty beverage and pastry are ready.';
      return;
    }

    const currentStage = stages[currentStageIdx];
    updatePipelineStage(currentStage);

    if (currentStage === 'brewing') {
      waitMinDisplay.textContent = '~3';
      notesDetail.textContent = 'Single-origin beans freshly ground and 9-bar espresso extraction running.';
    } else if (currentStage === 'artistry') {
      waitMinDisplay.textContent = '~1';
      notesDetail.textContent = 'Velvety micro-foamed oat milk steamed to 62°C and poured with latte art.';
    }
  }, 12000); // Transitions every 12 seconds for an engaging demo
}

function checkExistingOrderSession() {
  const saved = sessionStorage.getItem('current_cafe_order');
  if (saved) {
    try {
      const order = JSON.parse(saved);
      state.currentOrder = order;
      activateOrderPipeline(order);
    } catch (e) {
      console.warn('Could not parse saved session order:', e);
    }
  }
}

/**
 * Flavor Discovery & Mood Sommelier
 */
async function generateDiscoveryRecommendation() {
  const mood = document.getElementById('moodSelect').value;
  const dietary = document.getElementById('dietarySelect').value;
  const caffeine = document.getElementById('caffeineSelect').value;
  const btn = document.getElementById('getDiscoveryBtn');

  try {
    btn.disabled = true;
    btn.innerHTML = '<span>✨ Gemini Consulting Flavor Chemistry...</span>';

    const res = await fetch('/api/ai/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood, dietary_pref: dietary, caffeine_pref: caffeine }),
    });

    const data = await res.json();
    if (data.status === 'success' && data.recommendation) {
      renderDiscoveryResult(data.recommendation);
    }
  } catch (err) {
    console.error('Discovery recommendation failed:', err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>✨ Ask Gemini Sommelier</span>';
  }
}

function renderDiscoveryResult(rec) {
  document.getElementById('recDrinkTitle').textContent = rec.drink_name || 'Artisan Pour Over';
  document.getElementById('recPastryTitle').textContent = rec.pairing_name || 'Almond Croissant';
  document.getElementById('recRationale').textContent = rec.pairing_rationale || '';
  document.getElementById('recBaristaTip').innerHTML = `<strong>Barista Pro-Tip:</strong> ${rec.barista_tip || 'Enjoy slowly for optimal aromatics.'}`;

  // Flavor chips
  const chipsContainer = document.getElementById('flavorChipsList');
  if (chipsContainer && rec.tasting_notes) {
    chipsContainer.innerHTML = rec.tasting_notes
      .map((note) => `<span class="flavor-chip">✦ ${note}</span>`)
      .join('');
  }
}

function addRecommendedDrinkToCart() {
  const drinkTitle = document.getElementById('recDrinkTitle').textContent;
  const matched = state.menuItems.find((i) => i.name.toLowerCase() === drinkTitle.toLowerCase()) || state.menuItems[0];
  if (matched) addItemToCart(matched.id, 'Recommended by Gemini Sommelier');
}

function addRecommendedPastryToCart() {
  const pastryTitle = document.getElementById('recPastryTitle').textContent;
  const matched = state.menuItems.find((i) => i.name.toLowerCase() === pastryTitle.toLowerCase()) || state.menuItems[5];
  if (matched) addItemToCart(matched.id, 'Recommended pairing');
}

/**
 * Connect People: The Café Commons
 */
async function fetchCommunalPatrons() {
  try {
    const res = await fetch('/api/social/patrons');
    const data = await res.json();
    if (data.status === 'success') {
      state.activePatrons = data.patrons;
      renderPatrons();
      
      const patronCountEl = document.getElementById('activePatronsDisplay');
      if (patronCountEl) {
        patronCountEl.textContent = `${data.patrons.length} Creators`;
      }
    }
  } catch (err) {
    console.error('Failed to load patrons:', err);
  }
}

function renderPatrons() {
  const grid = document.getElementById('patronsGrid');
  if (!grid) return;

  if (state.activePatrons.length === 0) {
    grid.innerHTML = '<p class="empty-sub">No communal cards active yet. Be the first to join!</p>';
    return;
  }

  grid.innerHTML = state.activePatrons.map((p) => {
    const interestsHtml = (p.skills_interests || []).map(i => `<span class="interest-chip">${i}</span>`).join('');
    return `
      <div class="patron-card" data-patron-id="${p.id}">
        <div class="patron-card-header">
          <div class="patron-avatar">${p.avatar_emoji || '☕'}</div>
          <div>
            <h4 class="patron-name">${p.name}</h4>
            <span class="patron-table">${p.table_number}</span>
          </div>
        </div>
        <div class="patron-open-badge">
          <span>●</span> ${p.open_for}
        </div>
        <div class="patron-topic-box">
          <span class="topic-label">Currently Working On:</span>
          <p class="topic-text">${p.focus_topic}</p>
        </div>
        <div class="patron-interests">${interestsHtml}</div>
        <button type="button" class="btn-spark-icebreaker" onclick="triggerIcebreaker(${p.id})">
          ✨ Spark AI Icebreaker
        </button>
      </div>
    `;
  }).join('');
}

function openJoinLoungeModal() {
  document.getElementById('joinLoungeModal').classList.add('open');
}

function closeJoinLoungeModal() {
  document.getElementById('joinLoungeModal').classList.remove('open');
}

async function handleJoinLoungeSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('patronNameInput').value.trim();
  const table = document.getElementById('patronTableInput').value.trim();
  const topic = document.getElementById('patronTopicInput').value.trim();
  const openFor = document.getElementById('patronOpenForSelect').value;
  const skills = document.getElementById('patronSkillsInput').value.trim();

  try {
    const res = await fetch('/api/social/patrons', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        table_number: table,
        focus_topic: topic,
        open_for: openFor,
        skills_interests: skills,
        avatar_emoji: '💡',
      }),
    });
    const data = await res.json();
    if (data.status === 'success') {
      closeJoinLoungeModal();
      await fetchCommunalPatrons();
    }
  } catch (err) {
    console.error('Failed to register patron:', err);
  }
}

/**
 * Trigger AI Icebreaker Spark
 */
async function triggerIcebreaker(targetPatronId) {
  const modal = document.getElementById('icebreakerModal');
  const loading = document.getElementById('icebreakerLoading');
  const content = document.getElementById('icebreakerContent');

  modal.classList.add('open');
  loading.style.display = 'block';
  content.style.display = 'none';

  // Find target patron and default self
  const myPatron = state.activePatrons[0] || { id: 1 };
  const target = state.activePatrons.find((p) => p.id === targetPatronId) || state.activePatrons[1];

  try {
    const res = await fetch('/api/social/icebreaker', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patron_a_id: myPatron.id, patron_b_id: target.id }),
    });

    const data = await res.json();
    if (data.status === 'success' && data.icebreaker) {
      const ib = data.icebreaker;
      document.getElementById('icebreakerSharedThread').textContent = ib.shared_thread;
      document.getElementById('icebreakerPromptQuote').textContent = ib.icebreaker_prompt;
      document.getElementById('icebreakerActivityText').textContent = ib.suggested_activity;

      loading.style.display = 'none';
      content.style.display = 'block';
    }
  } catch (err) {
    console.error('Icebreaker spark error:', err);
    loading.innerHTML = '<p class="empty-sub">Could not generate spark right now. Try saying hello directly!</p>';
  }
}

function closeIcebreakerModal() {
  document.getElementById('icebreakerModal').classList.remove('open');
}

/**
 * Understand the Room: Live Table Feedback
 */
function setStarRating(score) {
  state.starRating = score;
  document.getElementById('fbSentimentScore').value = score;
  document.querySelectorAll('.star-btn').forEach((btn) => {
    const s = parseInt(btn.dataset.score, 10);
    btn.classList.toggle('active', s <= score);
  });
}

async function handleFeedbackSubmit(event) {
  event.preventDefault();
  const table = document.getElementById('fbTableNum').value.trim();
  const score = parseInt(document.getElementById('fbSentimentScore').value, 10);
  const noise = document.getElementById('fbNoise').value;
  const temp = document.getElementById('fbTemp').value;
  const vibe = document.getElementById('fbVibe').value;
  const comment = document.getElementById('fbComment').value.trim();

  try {
    const res = await fetch('/api/room/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        table_number: table,
        sentiment_score: score,
        noise_rating: noise,
        temperature_rating: temp,
        vibe_tag: vibe,
        customer_comment: comment,
      }),
    });

    const data = await res.json();
    if (data.status === 'success') {
      const toast = document.getElementById('feedbackToastMsg');
      toast.textContent = '✓ Pulse sent to baristas! Thank you.';
      setTimeout(() => { toast.textContent = ''; }, 4000);
      document.getElementById('tableFeedbackForm').reset();
      setStarRating(5);
    }
  } catch (err) {
    console.error('Feedback submit failed:', err);
  }
}

async function fetchRoomTelemetry() {
  try {
    const res = await fetch('/api/room/pulse');
    const data = await res.json();
    if (data.status === 'success' && data.pulse) {
      const vibeEl = document.getElementById('currentVibeDisplay');
      if (vibeEl) vibeEl.textContent = data.pulse.room_vibe_label || 'Cozy & Focused';
    }
  } catch (err) {
    console.warn('Telemetry load failed:', err);
  }
}

/**
 * Google Cloud Architecture Modal & API Key Settings
 */
function openCloudModal() {
  document.getElementById('cloudModal').classList.add('open');
}

function closeCloudModal() {
  document.getElementById('cloudModal').classList.remove('open');
}

async function saveGeminiApiKey() {
  const keyInput = document.getElementById('geminiKeyInput');
  const key = keyInput.value.trim();
  const feedback = document.getElementById('keyFeedbackMsg');

  if (!key) {
    feedback.textContent = 'Please enter an API key.';
    feedback.style.color = '#ef4444';
    return;
  }

  try {
    const res = await fetch('/api/config/key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key }),
    });

    const data = await res.json();
    if (data.status === 'success') {
      feedback.textContent = '✓ Key activated! Live Gemini model engaged.';
      feedback.style.color = '#4ade80';
      document.getElementById('aiStatusLabel').textContent = 'Gemini Live Active';
      setTimeout(() => closeCloudModal(), 1500);
    }
  } catch (err) {
    feedback.textContent = 'Failed to activate key.';
    feedback.style.color = '#ef4444';
  }
}

function setupSmoothScrolling() {
  document.querySelectorAll('.anchor-link').forEach((link) => {
    link.addEventListener('click', (e) => {
      document.querySelectorAll('.anchor-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    });
  });
}
