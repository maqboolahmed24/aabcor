(() => {
  const navLinks = Array.from(document.querySelectorAll('nav a[href^="#"]'));
  const sections = navLinks
    .map(a => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);
  const setActive = (id) => {
    for (const a of navLinks) {
      const match = a.getAttribute('href') === id;
      a.toggleAttribute('aria-current', match);
      a.classList.toggle('text-ink-900', match);
    }
  };
  const io = new IntersectionObserver((entries) => {
    const visible = entries
      .filter(e => e.isIntersecting)
      .sort((a,b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible) setActive('#'+visible.target.id);
  }, { rootMargin: '-20% 0px -70% 0px', threshold: [0, .25, .5, .75, 1] });
  sections.forEach(s => io.observe(s));

  // Prevent hash from sticking in the URL so refresh doesn't jump to a section.
  // Intercept nav clicks to scroll without updating location.hash.
  navLinks.forEach(a => {
    a.addEventListener('click', (e) => {
      const href = a.getAttribute('href');
      if (href && href.startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target && typeof target.scrollIntoView === 'function') {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        if (history && typeof history.replaceState === 'function') {
          try { history.replaceState(null, '', location.pathname + location.search); } catch {}
        }
      }
    });
  });

  // If a hash is present from a previous visit, clear it (do not change scroll).
  if (location.hash && history && typeof history.replaceState === 'function') {
    try { history.replaceState(null, '', location.pathname + location.search); } catch {}
  }

  // Simple "More" menu for navbar to reduce clutter
  const moreBtn = document.getElementById('nav-more-btn');
  const moreMenu = document.getElementById('nav-more-menu');
  if (moreBtn && moreMenu) {
    const closeMenu = () => {
      if (!moreMenu.classList.contains('hidden')) {
        moreMenu.classList.add('hidden');
        moreBtn.setAttribute('aria-expanded', 'false');
      }
    };
    moreBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const isHidden = moreMenu.classList.contains('hidden');
      if (isHidden) {
        moreMenu.classList.remove('hidden');
        moreBtn.setAttribute('aria-expanded', 'true');
        // focus first item for accessibility
        const first = moreMenu.querySelector('a');
        if (first) first.focus();
      } else {
        closeMenu();
      }
    });
    document.addEventListener('click', (e) => {
      if (!moreMenu.contains(e.target) && e.target !== moreBtn && !moreBtn.contains(e.target)) {
        closeMenu();
      }
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeMenu();
      // simple up/down navigation
      if (!moreMenu.classList.contains('hidden') && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) {
        e.preventDefault();
        const items = Array.from(moreMenu.querySelectorAll('a'));
        const idx = items.indexOf(document.activeElement);
        let next = 0;
        if (e.key === 'ArrowDown') next = idx < items.length - 1 ? idx + 1 : 0;
        else next = idx > 0 ? idx - 1 : items.length - 1;
        items[next].focus();
      }
    });
    // Close on link click
    Array.from(moreMenu.querySelectorAll('a')).forEach(el => {
      el.addEventListener('click', () => closeMenu());
    });
  }

  // Flow tooltip interactions
  const flow = document.querySelector('.flow');
  if (flow) {
    const svg = flow.querySelector('svg');
    const tooltip = flow.querySelector('#flow-tooltip');
    const stages = flow.querySelectorAll('.stage');
    let activeStage = null;
    const placeTooltip = (target) => {
      if (!svg || !tooltip) return;
      const rectEl = target.querySelector('.node') || target;
      const br = rectEl.getBoundingClientRect();
      const cr = flow.getBoundingClientRect();
      let cx = br.left + br.width / 2 - cr.left;
      let cy = br.top - cr.top; // position above the node
      // Clamp horizontally inside the flow container
      const minX = 16, maxX = cr.width - 16;
      cx = Math.max(minX, Math.min(cx, maxX));
      // Ensure tooltip doesn't go off the top edge
      cy = Math.max(24, cy);
      tooltip.style.left = `${Math.round(cx)}px`;
      tooltip.style.top = `${Math.round(cy)}px`;
    };
    const showTip = (target) => {
      const tip = target.getAttribute('data-tip') || '';
      if (tooltip) {
        tooltip.textContent = tip;
        placeTooltip(target);
        tooltip.classList.add('show');
        tooltip.setAttribute('aria-hidden', 'false');
      }
    };
    const openTip = (target) => {
      showTip(target);
      activeStage = target;
    };
    const closeTip = () => {
      if (tooltip) {
        tooltip.classList.remove('show');
        tooltip.setAttribute('aria-hidden', 'true');
      }
      activeStage = null;
    };
    stages.forEach((g) => {
      g.addEventListener('mouseenter', () => {
        // Hover shows non-sticky tooltip
        showTip(g);
      });
      g.addEventListener('mousemove', () => {
        placeTooltip(g);
      });
      g.addEventListener('mouseleave', () => {
        // only close hover tooltips if not manually activated via tap
        if (!activeStage) closeTip();
      });
      // Keyboard support: Enter/Space toggles
      g.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          if (activeStage === g) closeTip(); else openTip(g);
        }
        if (e.key === 'Escape') closeTip();
      });
      // Tap/click to toggle tooltip on mobile
      g.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (activeStage === g) {
          closeTip();
        } else {
          openTip(g);
        }
      });
      g.addEventListener('touchstart', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (activeStage === g) {
          closeTip();
        } else {
          openTip(g);
        }
      }, { passive: false });
    });
    // Close tooltip on outside tap/click
    document.addEventListener('click', (e) => {
      if (!flow.contains(e.target)) closeTip();
    });
    document.addEventListener('touchstart', (e) => {
      if (!flow.contains(e.target)) closeTip();
    }, { passive: true });
  }
})();
