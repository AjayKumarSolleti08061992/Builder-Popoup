/**
 * The Café Companion — Barista Floor & Kitchen Operations Script
 * Powers real-time room sentiment analytics, AI floor directives,
 * and kitchen order lifecycle transitions (Placed -> Brewing -> Ready -> Served).
 */

async function refreshBaristaDashboard() {
  await Promise.all([
    fetchKitchenOrders(),
    fetchRoomSentimentMatrix(),
  ]);
}

/**
 * Fetch and render kitchen preparation orders
 */
async function fetchKitchenOrders() {
  const container = document.getElementById('kitchenOrdersGrid');
  const countEl = document.getElementById('kitchenQueueCount');
  if (!container) return;

  try {
    const res = await fetch('/api/orders');
    const data = await res.json();

    if (data.status === 'success') {
      const orders = data.orders || [];
      const activeOrders = orders.filter((o) => o.status !== 'served');
      if (countEl) countEl.textContent = activeOrders.length;

      if (orders.length === 0) {
        container.innerHTML = '<div class="empty-sub">No tickets in the kitchen stream right now.</div>';
        return;
      }

      container.innerHTML = orders.map((order) => {
        const itemsHtml = (order.items || []).map(
          (i) => `<div>• <strong>${i.quantity}x</strong> ${i.name}</div>`
        ).join('');

        let actionBtnHtml = '';
        if (order.status === 'placed') {
          actionBtnHtml = `
            <button type="button" class="btn-ticket-action brew" onclick="advanceOrderStatus(${order.id}, 'brewing')">
              ☕ Start Brewing
            </button>
          `;
        } else if (order.status === 'brewing') {
          actionBtnHtml = `
            <button type="button" class="btn-ticket-action ready-btn" onclick="advanceOrderStatus(${order.id}, 'ready')">
              ✓ Mark Ready
            </button>
          `;
        } else if (order.status === 'ready') {
          actionBtnHtml = `
            <button type="button" class="btn-ticket-action served-btn" onclick="advanceOrderStatus(${order.id}, 'served')">
              📦 Complete / Served
            </button>
          `;
        } else {
          actionBtnHtml = `<span class="empty-sub">✓ Order Complete</span>`;
        }

        return `
          <div class="kitchen-ticket-card ${order.status}" id="ticket-${order.id}">
            <div class="kitchen-ticket-header">
              <span class="ticket-code">#${order.order_code}</span>
              <span class="ticket-status-pill ${order.status}">${order.status}</span>
            </div>
            <div class="ticket-customer-info">
              <strong>${order.customer_name}</strong> • ${order.table_number}
              ${order.special_notes ? `<div style="color: var(--accent-gold-light); font-size: 0.78rem; margin-top: 0.2rem;">📝 ${order.special_notes}</div>` : ''}
            </div>
            <div class="ticket-items-list">
              ${itemsHtml}
            </div>
            <div class="ticket-actions-row">
              ${actionBtnHtml}
            </div>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Failed to load kitchen orders:', err);
  }
}

/**
 * Advance order status in the database
 */
async function advanceOrderStatus(orderId, nextStatus) {
  try {
    const res = await fetch(`/api/orders/${orderId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus }),
    });

    const data = await res.json();
    if (data.status === 'success') {
      await fetchKitchenOrders();

      // If user also has this order in active session, sync it!
      const saved = sessionStorage.getItem('current_cafe_order');
      if (saved) {
        const curr = JSON.parse(saved);
        if (curr.id === orderId) {
          curr.status = nextStatus;
          sessionStorage.setItem('current_cafe_order', JSON.stringify(curr));
          if (window.updatePipelineStage) {
            window.updatePipelineStage(nextStatus);
          }
        }
      }
    }
  } catch (err) {
    console.error('Failed to advance order status:', err);
  }
}

/**
 * Fetch and render room sentiment matrix & Gemini floor directives
 */
async function fetchRoomSentimentMatrix() {
  try {
    const res = await fetch('/api/room/pulse');
    const data = await res.json();

    if (data.status === 'success' && data.pulse) {
      const pulse = data.pulse;

      const pctEl = document.getElementById('baristaSentimentPct');
      const vibeEl = document.getElementById('baristaVibeLabel');
      const ratingEl = document.getElementById('baristaAvgRating');
      const summaryEl = document.getElementById('baristaPulseSummary');
      const directivesList = document.getElementById('baristaDirectivesList');

      if (pctEl) pctEl.textContent = `${pulse.overall_sentiment_pct}%`;
      if (vibeEl) vibeEl.textContent = pulse.room_vibe_label || 'Cozy & Focused';
      if (ratingEl) ratingEl.textContent = `Average Rating: ★ ${pulse.average_rating || 4.8} / 5.0`;
      if (summaryEl) summaryEl.textContent = pulse.pulse_summary || '';

      if (directivesList && pulse.staff_actions) {
        directivesList.innerHTML = pulse.staff_actions.map(
          (act) => `
            <li class="directive-item">
              <span class="directive-check">✓</span>
              <span>${act}</span>
            </li>
          `
        ).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load room pulse matrix:', err);
  }
}

/**
 * Trigger staff action confirmation toast
 */
function triggerStaffAction(actionMessage) {
  alert(`Floor Action Logged: ${actionMessage}`);
}

// Attach globally
window.refreshBaristaDashboard = refreshBaristaDashboard;
window.advanceOrderStatus = advanceOrderStatus;
window.triggerStaffAction = triggerStaffAction;
