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

  const rateStops = [0.75, 1, 1.25, 1.5, 1.75, 2];

  const formatRate = (rate) => {
    const compact = Number(rate.toFixed(2));
    return `${String(compact).replace(".", ",")}×`;
  };

  const makeButton = (label, accessibleName) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dialogue-control-button";
    button.textContent = label;
    button.setAttribute("aria-label", accessibleName);
    button.title = accessibleName;
    return button;
  };

  const setAvailable = (button, available) => {
    button.classList.toggle("is-disabled", !available);
    button.setAttribute("aria-disabled", available ? "false" : "true");
  };

  const installPlaybackControls = (root, audio) => {
    const chapterStrip = root.querySelector(".dialogue-chapters");
    if (!chapterStrip || root.querySelector(".dialogue-navigation")) return;

    const navigation = document.createElement("div");
    navigation.className = "dialogue-navigation";

    const playbackTools = document.createElement("div");
    playbackTools.className = "dialogue-playback-tools";
    playbackTools.setAttribute("role", "group");
    playbackTools.setAttribute("aria-label", "Controles adicionales del audio");

    const rewind = makeButton("−10 s", "Retroceder 10 segundos");
    const forward = makeButton("+10 s", "Avanzar 10 segundos");
    const separator = document.createElement("span");
    separator.className = "dialogue-controls-separator";
    separator.setAttribute("aria-hidden", "true");
    separator.textContent = "·";

    const rateGroup = document.createElement("div");
    rateGroup.className = "dialogue-rate-controls";
    rateGroup.setAttribute("role", "group");
    rateGroup.setAttribute("aria-label", "Velocidad de reproducción");

    const rateDown = makeButton("−", "Disminuir la velocidad");
    const rateOutput = document.createElement("output");
    rateOutput.className = "dialogue-rate-output";
    rateOutput.setAttribute("aria-live", "polite");
    const rateUp = makeButton("+", "Aumentar la velocidad");

    if ("preservesPitch" in audio) audio.preservesPitch = true;
    if ("webkitPreservesPitch" in audio) audio.webkitPreservesPitch = true;

    const closestRateIndex = () => rateStops.reduce((closest, rate, index) => (
      Math.abs(rate - audio.playbackRate) < Math.abs(rateStops[closest] - audio.playbackRate)
        ? index
        : closest
    ), 0);

    const syncRate = () => {
      const index = closestRateIndex();
      const rate = rateStops[index];
      rateOutput.textContent = formatRate(rate);
      rateOutput.setAttribute("aria-label", `Velocidad ${formatRate(rate)}`);
      setAvailable(rateDown, index > 0);
      setAvailable(rateUp, index < rateStops.length - 1);
    };

    const changeRate = (direction) => {
      const currentIndex = closestRateIndex();
      const nextIndex = Math.min(
        rateStops.length - 1,
        Math.max(0, currentIndex + direction),
      );
      if (nextIndex === currentIndex) return;
      const rate = rateStops[nextIndex];
      audio.defaultPlaybackRate = rate;
      audio.playbackRate = rate;
      syncRate();
    };

    const syncSeekButtons = () => {
      const ready = Number.isFinite(audio.duration);
      setAvailable(rewind, ready && audio.currentTime > 0.05);
      setAvailable(forward, ready && audio.currentTime < audio.duration - 0.3);
    };

    const skipBy = (seconds) => {
      if (!Number.isFinite(audio.duration)) return;
      const upperBound = Math.max(0, audio.duration - 0.25);
      audio.currentTime = Math.min(
        upperBound,
        Math.max(0, audio.currentTime + seconds),
      );
      syncSeekButtons();
    };

    rewind.addEventListener("click", () => {
      if (rewind.getAttribute("aria-disabled") !== "true") skipBy(-10);
    });
    forward.addEventListener("click", () => {
      if (forward.getAttribute("aria-disabled") !== "true") skipBy(10);
    });
    rateDown.addEventListener("click", () => {
      if (rateDown.getAttribute("aria-disabled") !== "true") changeRate(-1);
    });
    rateUp.addEventListener("click", () => {
      if (rateUp.getAttribute("aria-disabled") !== "true") changeRate(1);
    });

    audio.addEventListener("ratechange", syncRate);
    audio.addEventListener("loadedmetadata", syncSeekButtons);
    audio.addEventListener("timeupdate", syncSeekButtons);
    audio.addEventListener("seeking", syncSeekButtons);
    root.addEventListener("keydown", (event) => {
      const playerKeys = [" ", "Spacebar", "Enter", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"];
      if (!playerKeys.includes(event.key)) return;
      event.stopPropagation();
      if (
        (event.key === " " || event.key === "Spacebar" || event.key === "Enter")
        && event.target instanceof HTMLButtonElement
      ) {
        event.preventDefault();
        event.target.click();
      }
    });

    rateGroup.append(rateDown, rateOutput, rateUp);
    playbackTools.append(rewind, forward, separator, rateGroup);
    chapterStrip.before(navigation);
    navigation.append(chapterStrip, playbackTools);
    syncRate();
    syncSeekButtons();
  };

  const initialise = (root) => {
    const audio = root.querySelector("audio");
    if (!audio) {
      root.classList.add("dialogue-unavailable");
      return;
    }

    installPlaybackControls(root, audio);

    const track = tracks[root.dataset.track];
    if (!track || !Array.isArray(track.turns) || !track.turns.length) {
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
