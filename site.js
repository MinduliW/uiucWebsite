document.addEventListener('DOMContentLoaded', () => {
  // "Space for ___" rotating word
  const word = document.getElementById('rotatingWord');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (word && !reduceMotion) {
    const words = ['good', 'servicing', 'safety', 'us'];
    let i = 0;
    setInterval(() => {
      word.classList.add('is-changing');
      setTimeout(() => {
        i = (i + 1) % words.length;
        word.textContent = words[i];
        word.classList.remove('is-changing');
      }, 300);
    }, 2200);
  }

  // Debris videos: start offset, segment loop and playback speed
  document.querySelectorAll('.debris-video').forEach((video) => {
    const start = parseFloat(video.dataset.startAt || '18');
    const end = parseFloat(video.dataset.endAt || '50');
    const rate = parseFloat(video.dataset.playbackRate || '1');
    video.addEventListener('loadedmetadata', () => {
      if (start >= 0 && start < video.duration) video.currentTime = start;
      if (rate > 0) video.playbackRate = rate;
      if (start < video.duration && end <= video.duration && end > start) {
        video.addEventListener('timeupdate', () => {
          if (video.currentTime >= end) video.currentTime = start;
        });
      }
    });
  });
});
