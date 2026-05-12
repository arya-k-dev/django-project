function getCookie(name) {
  const parts = `; ${document.cookie}`.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value || '';
  return div.innerHTML;
}

function setButtonLoading(button, isLoading) {
  if (!button) return;
  button.disabled = isLoading;
  const label = button.querySelector('.btn-label');
  const loading = button.querySelector('.btn-loading');
  if (label && loading) {
    label.classList.toggle('hidden', isLoading);
    loading.classList.toggle('hidden', !isLoading);
  }
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('hidden');
    const firstField = modal.querySelector('textarea, input, button');
    if (firstField) setTimeout(() => firstField.focus(), 80);
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add('hidden');
}

function initMobileNavigation() {
  const toggle = document.getElementById('mobile-nav-toggle');
  const panel = document.getElementById('mobile-nav-panel');
  if (!toggle || !panel) return;

  toggle.addEventListener('click', () => {
    const isHidden = panel.classList.toggle('hidden');
    toggle.setAttribute('aria-expanded', String(!isHidden));
  });
}

function initAlerts() {
  document.querySelectorAll('.alert').forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.25s ease, transform 0.25s ease';
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 260);
    }, 4500);
  });
}

function initTabs() {
  document.querySelectorAll('[data-tabs]').forEach((group) => {
    const tabs = group.querySelectorAll('.tab-btn');
    const panes = group.querySelectorAll('.tab-pane');
    tabs.forEach((button) => {
      button.addEventListener('click', () => {
        tabs.forEach((tab) => tab.classList.remove('active'));
        panes.forEach((pane) => pane.classList.remove('active'));
        button.classList.add('active');
        const pane = group.querySelector(`#${button.dataset.tab}`);
        if (pane) pane.classList.add('active');
      });
    });
  });
}

function initModals() {
  document.addEventListener('click', (event) => {
    const requestButton = event.target.closest('[data-open-request-modal]');
    if (requestButton) {
      const form = document.getElementById('send-request-form');
      const title = document.getElementById('modal-title');
      if (form) form.action = `/matching/send/${requestButton.dataset.userId}/`;
      if (title) title.textContent = `Connect with ${requestButton.dataset.userName}`;
      openModal('send-request-modal');
      return;
    }

    if (event.target.closest('[data-open-profile-request-modal]')) {
      openModal('profile-request-modal');
      return;
    }

    if (event.target.closest('[data-close-modal]')) {
      event.target.closest('[data-modal]')?.classList.add('hidden');
      return;
    }

    const backdrop = event.target.closest('.modal-backdrop');
    if (backdrop && event.target === backdrop) {
      backdrop.classList.add('hidden');
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      document.querySelectorAll('[data-modal]:not(.hidden)').forEach((modal) => modal.classList.add('hidden'));
    }
  });
}

function initConfirmForms() {
  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });
}

function initPasswordToggles() {
  document.querySelectorAll('[data-password-toggle]').forEach((button) => {
    const shell = button.closest('.auth-input-shell');
    const input = shell?.querySelector('input[type="password"], input[type="text"]');
    if (!input) return;

    button.addEventListener('click', () => {
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      button.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
      const icon = button.querySelector('i');
      if (icon) {
        icon.classList.toggle('fa-eye', !isHidden);
        icon.classList.toggle('fa-eye-slash', isHidden);
      }
    });
  });
}

function initSessionWorkflow() {
  const filterButtons = document.querySelectorAll('[data-session-filter]');
  const cards = document.querySelectorAll('[data-session-phase]');

  function applyFilter(filter) {
    cards.forEach((card) => {
      const visible = filter === 'all' || card.dataset.sessionPhase === filter;
      card.classList.toggle('hidden', !visible);
    });

    document.querySelectorAll('.tab-pane').forEach((pane) => {
      const paneCards = Array.from(pane.querySelectorAll('[data-session-phase]'));
      const hasVisibleCards = paneCards.some((card) => !card.classList.contains('hidden'));
      const empty = pane.querySelector('.session-filter-empty');
      if (empty) empty.classList.toggle('hidden', hasVisibleCards || !paneCards.length || filter === 'all');
    });
  }

  filterButtons.forEach((button) => {
    button.addEventListener('click', () => {
      filterButtons.forEach((item) => item.classList.remove('active'));
      button.classList.add('active');
      applyFilter(button.dataset.sessionFilter || 'all');
    });
  });

  document.querySelectorAll('[data-open-reschedule]').forEach((button) => {
    button.addEventListener('click', () => {
      const form = document.getElementById('reschedule-form');
      if (!form) return;
      form.action = button.dataset.action || '';
      document.getElementById('reschedule-date').value = button.dataset.date || '';
      document.getElementById('reschedule-time').value = button.dataset.time || '';
      document.getElementById('reschedule-duration').value = button.dataset.duration || '60';
      document.getElementById('reschedule-meeting-link').value = button.dataset.meetingLink || '';
      document.getElementById('reschedule-reason').value = '';
      openModal('reschedule-modal');
    });
  });

  function formatCountdown(ms) {
    const totalMinutes = Math.max(1, Math.floor(ms / 60000));
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return hours ? `${hours}h ${minutes}m` : `${minutes}m`;
  }

  function refreshCountdowns() {
    const now = Date.now();
    document.querySelectorAll('[data-countdown]').forEach((item) => {
      if (item.dataset.status !== 'accepted') return;
      const start = Date.parse(item.dataset.start);
      const end = Date.parse(item.dataset.end);
      const text = item.querySelector('span');
      if (!text || Number.isNaN(start) || Number.isNaN(end)) return;
      const card = item.closest('[data-session-phase]');
      const joinAction = card?.querySelector('[data-join-action]');
      const completeAction = card?.querySelector('[data-complete-action]');
      const liveMessage = card?.querySelector('[data-live-message]');
      const badge = card?.querySelector('.session-status-badge');

      if (now < start) {
        text.textContent = `Starts in ${formatCountdown(start - now)}`;
        joinAction?.classList.add('hidden');
        completeAction?.classList.add('hidden');
        liveMessage?.classList.add('hidden');
      } else if (now <= end) {
        text.textContent = `Live now - ${formatCountdown(end - now)} left`;
        card?.classList.add('session-live-card');
        if (card) card.dataset.sessionPhase = 'live';
        joinAction?.classList.remove('hidden');
        completeAction?.classList.add('hidden');
        liveMessage?.classList.remove('hidden');
        if (badge) {
          badge.textContent = 'Live Now';
          badge.className = 'session-status-badge status-live_now';
        }
      } else {
        text.textContent = 'Session time has passed';
        card?.classList.remove('session-live-card');
        if (card) card.dataset.sessionPhase = 'missed';
        joinAction?.classList.add('hidden');
        completeAction?.classList.remove('hidden');
        liveMessage?.classList.add('hidden');
        if (badge) {
          badge.textContent = 'Session Ended';
          badge.className = 'session-status-badge status-missed';
        }
      }
    });

    document.querySelectorAll('[data-session-progress]').forEach((panel) => {
      const start = Date.parse(panel.dataset.start);
      const end = Date.parse(panel.dataset.end);
      const bar = panel.querySelector('[data-progress-bar]');
      const label = panel.querySelector('[data-progress-label]');
      if (!bar || !label || Number.isNaN(start) || Number.isNaN(end)) return;
      const total = Math.max(1, end - start);
      const elapsed = Math.min(Math.max(now - start, 0), total);
      const percent = Math.round((elapsed / total) * 100);
      bar.style.width = `${percent}%`;

      if (now < start) {
        label.textContent = 'Not started yet';
      } else if (now <= end) {
        const completedMinutes = Math.floor(elapsed / 60000);
        const leftMinutes = Math.max(1, Math.ceil((end - now) / 60000));
        label.textContent = completedMinutes > 0
          ? `${completedMinutes} minutes completed - ${leftMinutes} minutes left`
          : `${leftMinutes} minutes left`;
      } else {
        label.textContent = 'Session ended';
      }
    });
  }

  if (document.querySelector('[data-countdown]')) {
    refreshCountdowns();
    window.setInterval(refreshCountdowns, 30000);
  }
}

function initScrollReveal() {
  const revealItems = Array.from(document.querySelectorAll('.reveal-on-scroll'));
  if (!revealItems.length) return;

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion || !('IntersectionObserver' in window)) {
    revealItems.forEach((item) => item.classList.add('reveal-visible'));
    return;
  }

  const staggerParents = [
    '.stagger-children',
    '.stats-grid',
    '.how-steps',
    '.category-grid',
    '.premium-category-grid',
    '.feature-grid',
    '.match-grid',
    '.skill-card-grid',
    '.category-skill-grid',
    '.category-user-grid',
    '.exchange-chip-grid',
    '.review-list',
  ];

  staggerParents.forEach((selector) => {
    document.querySelectorAll(selector).forEach((parent) => {
      Array.from(parent.querySelectorAll(':scope > .reveal-on-scroll')).forEach((item, index) => {
        item.style.setProperty('--reveal-delay', `${Math.min(index, 8) * 80}ms`);
      });
    });
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('reveal-visible');
      observer.unobserve(entry.target);
    });
  }, {
    threshold: 0.12,
    rootMargin: '0px 0px -8% 0px',
  });

  revealItems.forEach((item) => observer.observe(item));
}

function initSkillAutocomplete(inputId, hiddenId) {
  const input = document.getElementById(inputId);
  const hidden = document.getElementById(hiddenId);
  if (!input) return;

  let dropdown = null;
  let activeIndex = -1;
  let debounceTimer = null;

  function closeDropdown() {
    if (dropdown) dropdown.remove();
    dropdown = null;
    activeIndex = -1;
  }

  function positionParent() {
    const parent = input.parentElement;
    if (parent && getComputedStyle(parent).position === 'static') {
      parent.style.position = 'relative';
    }
    return parent;
  }

  function selectSkill(skill) {
    input.value = skill.name;
    if (hidden) hidden.value = skill.id;
    closeDropdown();
  }

  async function createSkill(name) {
    const response = await fetch('/skills/api/create/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({ name }),
    });
    if (!response.ok) return;
    const skill = await response.json();
    selectSkill(skill);
  }

  function makeItem(label, meta, onClick) {
    const item = document.createElement('button');
    item.type = 'button';
    item.className = 'skill-dropdown-item';
    const labelSpan = document.createElement('span');
    labelSpan.textContent = label;
    item.appendChild(labelSpan);
    if (meta) {
      const metaSpan = document.createElement('small');
      metaSpan.textContent = meta;
      item.appendChild(metaSpan);
    }
    item.addEventListener('click', onClick);
    return item;
  }

  function showDropdown(skills, query) {
    closeDropdown();
    dropdown = document.createElement('div');
    dropdown.className = 'skill-dropdown';

    if (skills.length) {
      skills.forEach((skill) => {
        dropdown.appendChild(makeItem(skill.name, skill.category || 'Skill', () => selectSkill(skill)));
      });
      dropdown.appendChild(makeItem(`Create "${query}"`, 'New skill', () => createSkill(query)));
    } else {
      dropdown.appendChild(makeItem(`Create "${query}"`, 'New skill', () => createSkill(query)));
    }

    positionParent().appendChild(dropdown);
  }

  input.addEventListener('input', () => {
    if (hidden) hidden.value = '';
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length < 2) {
      closeDropdown();
      return;
    }
    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch(`/skills/api/search/?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        showDropdown(data.skills || [], query);
      } catch (error) {
        closeDropdown();
      }
    }, 220);
  });

  input.addEventListener('keydown', (event) => {
    if (!dropdown) return;
    const items = Array.from(dropdown.querySelectorAll('.skill-dropdown-item'));
    if (!items.length) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      activeIndex = (activeIndex - 1 + items.length) % items.length;
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault();
      items[activeIndex].click();
      return;
    } else if (event.key === 'Escape') {
      closeDropdown();
      return;
    } else {
      return;
    }

    items.forEach((item, index) => item.classList.toggle('active', index === activeIndex));
  });

  document.addEventListener('click', (event) => {
    if (event.target !== input && !dropdown?.contains(event.target)) {
      closeDropdown();
    }
  });
}

function initSkillTypeToggle() {
  const input = document.getElementById('skill-type-input');
  const buttons = document.querySelectorAll('[data-skill-type]');
  if (!input || !buttons.length) return;

  function setType(type) {
    input.value = type;
    buttons.forEach((button) => button.classList.toggle('active', button.dataset.skillType === type));
  }

  buttons.forEach((button) => {
    button.addEventListener('click', () => setType(button.dataset.skillType));
  });
  setType(input.value || 'teach');

  document.querySelectorAll('[data-focus-skill]').forEach((button) => {
    button.addEventListener('click', () => document.getElementById('skill-name-input')?.focus());
  });
}

function appendMessage(message) {
  const container = document.getElementById('chat-messages');
  if (!container || container.querySelector(`[data-msg-id="${message.id}"]`)) return;

  document.getElementById('empty-chat-state')?.remove();

  const wrapper = document.createElement('div');
  wrapper.className = `message-wrapper ${message.is_mine ? 'mine' : ''}`;

  if (!message.is_mine && message.sender) {
    const author = document.createElement('span');
    author.className = 'message-author';
    author.textContent = message.sender;
    wrapper.appendChild(author);
  }

  const bubble = document.createElement('div');
  bubble.className = `message-bubble ${message.is_mine ? 'mine' : 'theirs'}`;
  bubble.dataset.msgId = message.id;
  bubble.dataset.timestamp = message.timestamp;
  bubble.innerHTML = `${escapeHtml(message.content).replace(/\n/g, '<br>')}<div class="message-time">${formatMessageTime(message.timestamp)}</div>`;
  wrapper.appendChild(bubble);
  container.appendChild(wrapper);
}

function formatMessageTime(timestamp) {
  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return '';
  return parsed.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function initChatPolling(conversationId) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  let lastTimestamp = null;
  const messages = container.querySelectorAll('.message-bubble');
  if (messages.length) {
    lastTimestamp = messages[messages.length - 1].dataset.timestamp;
  }

  async function poll() {
    const url = lastTimestamp
      ? `/messages/${conversationId}/poll/?since=${encodeURIComponent(lastTimestamp)}`
      : `/messages/${conversationId}/poll/`;
    try {
      const response = await fetch(url);
      if (!response.ok) return;
      const data = await response.json();
      (data.messages || []).forEach((message) => {
        appendMessage(message);
        lastTimestamp = message.timestamp;
      });
      if (data.messages && data.messages.length) {
        container.scrollTop = container.scrollHeight;
      }
    } catch (error) {
      // Polling is best-effort; the next interval will retry.
    }
  }

  container.scrollTop = container.scrollHeight;
  window.setInterval(poll, 3000);
}

function initMessageSend(conversationId) {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const button = document.getElementById('send-btn');
  const status = document.getElementById('chat-status');
  const container = document.getElementById('chat-messages');
  if (!form || !input || !button) return;

  let isSending = false;
  let lastSubmitted = { content: '', at: 0 };

  async function sendMessage() {
    const content = input.value.trim();
    const now = Date.now();
    if (!content || isSending) return;
    if (lastSubmitted.content === content && now - lastSubmitted.at < 2000) return;

    isSending = true;
    lastSubmitted = { content, at: now };
    setButtonLoading(button, true);
    if (status) status.textContent = '';

    try {
      const response = await fetch(`/messages/${conversationId}/send/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ content }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Message failed to send.');
      }

      appendMessage(data);
      input.value = '';
      input.style.height = 'auto';
      if (container) container.scrollTop = container.scrollHeight;
    } catch (error) {
      if (status) status.textContent = error.message || 'Message failed to send.';
    } finally {
      isSending = false;
      setButtonLoading(button, false);
      input.focus();
    }
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    sendMessage();
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initMobileNavigation();
  initAlerts();
  initTabs();
  initModals();
  initConfirmForms();
  initPasswordToggles();
  initSessionWorkflow();
  initScrollReveal();
});
