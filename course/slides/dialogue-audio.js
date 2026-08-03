(() => {
  const tracks = window.DIALOGUE_TRACKS || {};

  const formatTime = (seconds) => {
    const total = Math.max(0, Math.round(Number(seconds) || 0));
    const minutes = Math.floor(total / 60);
    return `${minutes}:${String(total % 60).padStart(2, "0")}`;
  };

  const turnAt = (turns, time) => {
    let low = 0;
    let high = turns.length - 1;
    let match = 0;
    while (low <= high) {
      const middle = Math.floor((low + high) / 2);
      if (turns[middle].start <= time) {
        match = middle;
        low = middle + 1;
      } else {
        high = middle - 1;
      }
    }
    return match;
  };

  const initialise = (root) => {
    const track = tracks[root.dataset.track];
    const audio = root.querySelector("audio");
    if (!track || !audio || !Array.isArray(track.turns) || !track.turns.length) {
      root.classList.add("dialogue-unavailable");
      return;
    }

    const speaker = root.querySelector("[data-dialogue-speaker]");
    const utterance = root.querySelector("[data-dialogue-utterance]");
    const next = root.querySelector("[data-dialogue-next]");
    const position = root.querySelector("[data-dialogue-position]");
    const duration = root.querySelector("[data-dialogue-duration]");
    const chapterButtons = [...root.querySelectorAll("[data-turn]")];
    let currentIndex = -1;

    if (duration) duration.textContent = formatTime(track.duration);

    const render = (index) => {
      const safeIndex = Math.min(Math.max(index, 0), track.turns.length - 1);
      if (safeIndex === currentIndex) return;
      currentIndex = safeIndex;
      const current = track.turns[safeIndex];
      const following = track.turns[safeIndex + 1];

      speaker.textContent = current.speaker;
      speaker.dataset.speaker = current.speaker;
      utterance.textContent = current.text;
      next.textContent = following ? `${following.speaker}: ${following.text}` : "Fin del diálogo";
      position.textContent = `${safeIndex + 1} / ${track.turns.length}`;

      chapterButtons.forEach((button, buttonIndex) => {
        const start = Number(button.dataset.turn);
        const nextStart = buttonIndex + 1 < chapterButtons.length
          ? Number(chapterButtons[buttonIndex + 1].dataset.turn)
          : Number.POSITIVE_INFINITY;
        const active = safeIndex >= start && safeIndex < nextStart;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-current", active ? "true" : "false");
      });
    };

    chapterButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const targetTurn = track.turns[Number(button.dataset.turn)];
        if (!targetTurn) return;
        audio.currentTime = targetTurn.start;
        audio.play().catch(() => {});
        render(Number(button.dataset.turn));
      });
    });

    audio.addEventListener("timeupdate", () => render(turnAt(track.turns, audio.currentTime)));
    audio.addEventListener("seeking", () => render(turnAt(track.turns, audio.currentTime)));
    audio.addEventListener("loadedmetadata", () => render(turnAt(track.turns, audio.currentTime)));
    render(0);
  };

  const initialiseAll = () => {
    document.querySelectorAll(".dialogue-player").forEach(initialise);
  };

  const pauseOutsideCurrentSlide = (event) => {
    document.querySelectorAll(".dialogue-player audio").forEach((audio) => {
      if (!event.currentSlide || !event.currentSlide.contains(audio)) audio.pause();
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialiseAll, { once: true });
  } else {
    initialiseAll();
  }

  if (window.Reveal) {
    window.Reveal.on("slidechanged", pauseOutsideCurrentSlide);
  }
})();
