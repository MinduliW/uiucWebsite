document.addEventListener('DOMContentLoaded', () => {

    // --- "Space for ___" rotating word animation ---
  const spaceWordEl = document.getElementById('spaceWord');
  if (spaceWordEl) {
    const words = ['good', 'servicing', 'sustainability','safety', 'us'];

    let idx = 0;

    const cycleWord = () => {
      const nextIdx = (idx + 1) % words.length;
      spaceWordEl.classList.add('is-changing');
      // Wait for fade-out transition before swapping text
      setTimeout(() => {
        spaceWordEl.textContent = words[nextIdx];
        spaceWordEl.classList.remove('is-changing');
        idx = nextIdx;
      }, 250);
    };

    // Start cycling every 2 seconds
    setInterval(cycleWord, 2000);
  }


  // --- Mobile nav toggle ---
  const nav = document.getElementById('nav');
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.querySelectorAll('.nav a[href^="#"]');

  if (navToggle) {
    navToggle.addEventListener('click', () => {
      nav.classList.toggle('open');
    });
  }

  // Close mobile nav when clicking a link
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      nav.classList.remove('open');
    });
  });

  // --- Scroll reveal for sections with .reveal ---
  const revealEls = document.querySelectorAll('.reveal');

  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );

    revealEls.forEach(el => revealObserver.observe(el));
  } else {
    // Fallback: just show everything
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  // --- Scrollspy: highlight nav item for the current section ---
  const sections = document.querySelectorAll('section[id]');

  if ('IntersectionObserver' in window) {
    const navObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const id = entry.target.id;
            navLinks.forEach(link => {
              const href = link.getAttribute('href');
              link.classList.toggle('active', href === `#${id}`);
            });
          }
        });
      },
      { rootMargin: '-50% 0px -50% 0px' } // middle of viewport
    );

    sections.forEach(section => navObserver.observe(section));
  }

  // --- Debris video start offset, segment loop & playback speed (multiple videos) ---
  const debrisVideos = document.querySelectorAll('.debris-video');
  debrisVideos.forEach((video) => {
    const startAt = parseFloat(video.getAttribute('data-start-at') || '18');
    const endAt = parseFloat(video.getAttribute('data-end-at') || '50');
    const playbackRate = parseFloat(video.getAttribute('data-playback-rate') || '1.0');

    video.addEventListener('loadedmetadata', () => {
      const duration = video.duration || 0;
      const startValid = !Number.isNaN(startAt) && startAt >= 0 && startAt < duration;
      const endValid = !Number.isNaN(endAt) && endAt > 0 && endAt <= duration && endAt > startAt;

      if (startValid) {
        video.currentTime = startAt;
      }
      if (!Number.isNaN(playbackRate) && playbackRate > 0) {
        video.playbackRate = playbackRate;
      }

      if (startValid && endValid) {
        video.addEventListener('timeupdate', () => {
          if (video.currentTime >= endAt) {
            video.currentTime = startAt;
          }
        });
      }
    });
  });
});
