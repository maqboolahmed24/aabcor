(() => {
  const navLinks = Array.from(document.querySelectorAll('nav a[href^="#"]'));
  const sectionMap = new Map();
  navLinks.forEach((link) => {
    const href = link.getAttribute('href');
    if (!href || !href.startsWith('#')) return;
    const id = href.slice(1);
    const section = document.getElementById(id);
    if (section && !sectionMap.has(id)) sectionMap.set(id, section);
  });
  const sections = Array.from(sectionMap.values());

  const navBar = document.querySelector('nav');
  const moreBtn = document.getElementById('nav-more-btn');
  const moreMenu = document.getElementById('nav-more-menu');
  const mobileToggle = document.getElementById('mobile-nav-toggle');
  const mobilePanel = document.getElementById('mobile-nav-panel');
  const reduceMotionQuery = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
  const prefersReducedMotion = () => (reduceMotionQuery ? reduceMotionQuery.matches : false);

  function setActive(id) {
    if (!id) return;
    let activeInMore = false;
    navLinks.forEach((link) => {
      const match = link.getAttribute('href') === id;
      if (match) {
        link.setAttribute('aria-current', 'page');
        link.classList.add('text-ink-900');
      } else {
        link.removeAttribute('aria-current');
        link.classList.remove('text-ink-900');
      }
      if (moreMenu && moreMenu.contains(link) && match) activeInMore = true;
    });
    if (moreBtn) {
      if (activeInMore) {
        moreBtn.setAttribute('data-active', 'true');
      } else {
        moreBtn.removeAttribute('data-active');
      }
    }
  }

  function scrollToTarget(target) {
    if (!target) return;
    const behavior = prefersReducedMotion() ? 'auto' : 'smooth';
    const navOffset = navBar ? navBar.offsetHeight + 12 : 0;
    const top = target.getBoundingClientRect().top + window.scrollY - navOffset;
    window.scrollTo({ top, left: 0, behavior });
  }

  function closeMobileNav() {
    if (!mobilePanel || !mobileToggle) return;
    mobilePanel.classList.remove('open');
    mobilePanel.hidden = true;
    mobilePanel.setAttribute('aria-hidden', 'true');
    mobileToggle.setAttribute('aria-expanded', 'false');
  }

  function openMobileNav() {
    if (!mobilePanel || !mobileToggle) return;
    mobilePanel.hidden = false;
    mobilePanel.classList.add('open');
    mobilePanel.setAttribute('aria-hidden', 'false');
    mobileToggle.setAttribute('aria-expanded', 'true');
  }

  function initSectionObserver() {
    if (!sections.length) return;
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        const visible = entries
          .filter(entry => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(`#${visible.target.id}`);
      }, { rootMargin: '-20% 0px -70% 0px', threshold: [0, 0.25, 0.5, 0.75, 1] });
      sections.forEach(section => observer.observe(section));
      return;
    }
    const handleScroll = () => {
      const offset = window.scrollY + window.innerHeight * 0.3;
      let current = sections[0];
      for (const section of sections) {
        if (section.offsetTop <= offset) current = section;
      }
      if (current) setActive(`#${current.id}`);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
  }

  function disableFlowAnimation(flowRoot) {
    if (!flowRoot || !prefersReducedMotion()) return;
    flowRoot.querySelectorAll('animate').forEach((el) => {
      if (el.parentNode) el.parentNode.removeChild(el);
    });
  }

  if (mobileToggle && mobilePanel) {
    mobileToggle.addEventListener('click', (event) => {
      event.preventDefault();
      const expanded = mobileToggle.getAttribute('aria-expanded') === 'true';
      if (expanded) closeMobileNav(); else openMobileNav();
    });
    document.addEventListener('click', (event) => {
      if (!mobilePanel.contains(event.target) && event.target !== mobileToggle && !mobileToggle.contains(event.target)) {
        closeMobileNav();
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMobileNav();
    });
    if (window.matchMedia) {
      const smQuery = window.matchMedia('(min-width: 640px)');
      const handleChange = (evt) => {
        if (evt.matches) closeMobileNav();
      };
      if (typeof smQuery.addEventListener === 'function') smQuery.addEventListener('change', handleChange);
      else if (typeof smQuery.addListener === 'function') smQuery.addListener(handleChange);
    }
  }

  navLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const href = link.getAttribute('href');
      if (!href || !href.startsWith('#')) return;
      event.preventDefault();
      const target = document.querySelector(href);
      scrollToTarget(target);
      setActive(href);
      if (history && typeof history.replaceState === 'function') {
        try { history.replaceState(null, '', href); } catch (err) {}
      }
      closeMobileNav();
      closeMoreMenu();
    });
  });

  const initialHash = location.hash && sectionMap.has(location.hash.slice(1))
    ? location.hash
    : (sections[0] ? `#${sections[0].id}` : null);
  if (initialHash) setActive(initialHash);

  initSectionObserver();

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
      let cy = br.top - cr.top;
      const minX = 16;
      const maxX = cr.width - 16;
      cx = Math.max(minX, Math.min(cx, maxX));
      cy = Math.max(24, cy);
      tooltip.style.left = `${Math.round(cx)}px`;
      tooltip.style.top = `${Math.round(cy)}px`;
    };

    const showTip = (target) => {
      const tip = target.getAttribute('data-tip') || '';
      if (!tooltip) return;
      tooltip.textContent = tip;
      placeTooltip(target);
      tooltip.hidden = false;
      tooltip.classList.add('show');
      tooltip.setAttribute('aria-hidden', 'false');
    };

    const openTip = (target) => {
      if (activeStage && activeStage !== target) {
        activeStage.setAttribute('aria-pressed', 'false');
      }
      target.setAttribute('aria-pressed', 'true');
      showTip(target);
      activeStage = target;
    };

    const closeTip = () => {
      if (tooltip) {
        tooltip.classList.remove('show');
        tooltip.setAttribute('aria-hidden', 'true');
        tooltip.hidden = true;
        tooltip.textContent = '';
      }
      if (activeStage) activeStage.setAttribute('aria-pressed', 'false');
      activeStage = null;
    };

    stages.forEach((stage) => {
      stage.addEventListener('mouseenter', () => {
        showTip(stage);
      });
      stage.addEventListener('mousemove', () => {
        placeTooltip(stage);
      });
      stage.addEventListener('mouseleave', () => {
        if (!activeStage) closeTip();
      });
      stage.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          if (activeStage === stage) closeTip(); else openTip(stage);
        }
        if (event.key === 'Escape') closeTip();
      });
      stage.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (activeStage === stage) {
          closeTip();
        } else {
          openTip(stage);
        }
      });
      stage.addEventListener('touchstart', (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (activeStage === stage) {
          closeTip();
        } else {
          openTip(stage);
        }
      }, { passive: false });
    });

    document.addEventListener('click', (event) => {
      if (!flow.contains(event.target)) closeTip();
    });
    document.addEventListener('touchstart', (event) => {
      if (!flow.contains(event.target)) closeTip();
    }, { passive: true });

    disableFlowAnimation(flow);
  if (reduceMotionQuery) {
    const handleMotionChange = (event) => {
      if (event.matches) disableFlowAnimation(flow);
    };
    if (typeof reduceMotionQuery.addEventListener === 'function') reduceMotionQuery.addEventListener('change', handleMotionChange);
    else if (typeof reduceMotionQuery.addListener === 'function') reduceMotionQuery.addListener(handleMotionChange);
  }
}

  function closeMoreMenu() {
    if (!moreMenu || !moreBtn) return;
    if (!moreMenu.hidden) {
      moreMenu.hidden = true;
      moreMenu.setAttribute('aria-hidden', 'true');
      moreBtn.setAttribute('aria-expanded', 'false');
    }
  }

  function openMoreMenu() {
    if (!moreMenu || !moreBtn) return;
    moreMenu.hidden = false;
    moreMenu.setAttribute('aria-hidden', 'false');
    moreBtn.setAttribute('aria-expanded', 'true');
    const first = moreMenu.querySelector('a');
    if (first) {
      try { first.focus({ preventScroll: true }); } catch { first.focus(); }
    }
  }

  if (moreMenu) {
    moreMenu.hidden = true;
    moreMenu.setAttribute('aria-hidden', 'true');
  }
  if (moreBtn && moreMenu) {
    moreBtn.addEventListener('click', (event) => {
      event.preventDefault();
      if (moreMenu.hidden) openMoreMenu(); else closeMoreMenu();
    });
    document.addEventListener('click', (event) => {
      if (!moreMenu.contains(event.target) && event.target !== moreBtn && !moreBtn.contains(event.target)) {
        closeMoreMenu();
      }
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeMoreMenu();
      if (!moreMenu.hidden && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
        event.preventDefault();
        const items = Array.from(moreMenu.querySelectorAll('a'));
        if (!items.length) return;
        const index = items.indexOf(document.activeElement);
        let next = 0;
        if (event.key === 'ArrowDown') {
          next = index >= 0 && index < items.length - 1 ? index + 1 : 0;
        } else {
          next = index > 0 ? index - 1 : items.length - 1;
        }
        items[next].focus();
      }
    });
    moreMenu.addEventListener('focusout', (event) => {
      if (!moreMenu.contains(event.relatedTarget)) closeMoreMenu();
    });
    Array.from(moreMenu.querySelectorAll('a')).forEach(link => {
      link.addEventListener('click', () => closeMoreMenu());
    });
  }

})();
