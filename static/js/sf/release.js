"use strict";
(() => {
    const player = document.querySelector('.music-player');
    const buttons = [...document.querySelectorAll('[data-track-url]')];
    if (!player || !buttons.length) return;

    const audio = player.querySelector('audio');
    const toggle = player.querySelector('.player-toggle');
    const seek = player.querySelector('.player-seek');
    const status = player.querySelector('.player-status');
    const loading = player.querySelector('.player-loading');
    const elapsed = player.querySelector('.player-elapsed');
    const remaining = player.querySelector('.player-remaining');
    const shuffleButton = player.querySelector('.player-shuffle');
    const repeatButton = player.querySelector('.player-repeat');
    const artist = player.dataset.artist;
    let current = -1;
    let shuffle = false;
    let repeat = 'off';
    let bag = [];
    let history = [];
    let generation = 0;
    let scrubbing = false;
    let returnFocus = null;

    const time = seconds => {
        const value = Math.max(0, Math.floor(seconds || 0));
        return `${Math.floor(value / 60).toString().padStart(2, '0')}:${(value % 60).toString().padStart(2, '0')}`;
    };
    const duration = () => Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : 0;
    const announce = message => { status.textContent = message; };
    const setLoading = active => { loading.hidden = !active; };
    const mediaSession = 'mediaSession' in navigator ? navigator.mediaSession : null;

    function syncPlayback() {
        const playing = current >= 0 && !audio.paused && !audio.ended;
        toggle.classList.toggle('is-playing', playing);
        toggle.setAttribute('aria-label', playing ? 'Pause' : 'Play');
        toggle.title = playing ? 'Pause' : 'Play';
        buttons.forEach((button, index) => {
            const active = index === current && playing;
            button.classList.toggle('is-playing', active);
            button.setAttribute('aria-pressed', String(active));
            button.setAttribute('aria-label', `${active ? 'Pause' : 'Play'} ${button.dataset.trackTitle}`);
        });
        if (mediaSession) mediaSession.playbackState = current < 0 ? 'none' : playing ? 'playing' : 'paused';
    }

    function syncTime() {
        const total = duration();
        const position = Number.isFinite(audio.currentTime) ? audio.currentTime : 0;
        elapsed.textContent = time(position);
        remaining.textContent = total ? `-${time(total - position)}` : '--:--';
        seek.disabled = !total;
        seek.max = total || 100;
        if (!scrubbing) seek.value = position;
        seek.style.setProperty('--progress', `${total ? Math.min(100, position / total * 100) : 0}%`);
        seek.setAttribute('aria-valuetext', `${time(position)} of ${total ? time(total) : 'unknown duration'}`);
    }

    async function play() {
        const request = ++generation;
        announce('');
        setLoading(audio.readyState < 3);
        try {
            await audio.play();
        } catch (error) {
            // A newer track, pause, or close can intentionally cancel play().
            if (request !== generation || player.hidden || error.name === 'AbortError') return;
            setLoading(false);
            announce(error.name === 'NotAllowedError' ? 'Press play to start listening.' : 'This track could not be loaded. Try again or download the release.');
            syncPlayback();
        }
    }

    function refillBag() {
        bag = buttons.map((_, index) => index).filter(index => index !== current);
        for (let index = bag.length - 1; index > 0; index--) {
            const other = Math.floor(Math.random() * (index + 1));
            [bag[index], bag[other]] = [bag[other], bag[index]];
        }
    }

    function select(index, remember = true) {
        if (remember && current >= 0 && current !== index) {
            history.push(current);
            if (history.length > 100) history.shift();
        }
        generation++;
        audio.pause();
        current = index;
        bag = bag.filter(item => item !== current);
        const track = buttons[current].dataset;
        player.hidden = false;
        document.body.classList.add('player-open');
        player.querySelector('.player-artist').textContent = artist;
        player.querySelector('.player-title').textContent = track.trackTitle;
        player.querySelector('.player-title').title = track.trackTitle;
        player.querySelector('.player-count').textContent = `${track.trackPosition} / ${player.dataset.total}`;
        audio.src = track.trackUrl;
        audio.load();
        syncPlayback();
        syncTime();
        if (mediaSession && 'MediaMetadata' in window) {
            mediaSession.metadata = new MediaMetadata({title: track.trackTitle, artist, album: player.dataset.album});
        }
        play();
    }

    function next(automatic = false) {
        if (current < 0) return;
        if (automatic && repeat === 'one') {
            audio.currentTime = 0;
            play();
            return;
        }
        if (shuffle) {
            if (!bag.length) {
                if (automatic && repeat === 'off') { syncPlayback(); return; }
                refillBag();
            }
            select(bag.pop() ?? current);
        } else if (current + 1 < buttons.length) {
            select(current + 1);
        } else if (!automatic || repeat === 'all') {
            select(0);
        } else {
            syncPlayback();
        }
    }

    function previous() {
        if (current < 0) return;
        if (audio.currentTime > 3) { audio.currentTime = 0; syncTime(); return; }
        select(history.pop() ?? (current - 1 + buttons.length) % buttons.length, false);
    }

    function togglePlayback() {
        if (audio.paused || audio.ended) {
            if (audio.ended) audio.currentTime = 0;
            if (audio.error) audio.load();
            play();
        } else {
            generation++;
            audio.pause();
        }
    }

    buttons.forEach((button, index) => {
        button.hidden = false;
        button.addEventListener('click', () => {
            returnFocus = button;
            if (current === index && !player.hidden) togglePlayback();
            else {
                history = [];
                select(index, false);
                if (shuffle) refillBag();
            }
        });
    });
    toggle.addEventListener('click', togglePlayback);
    player.querySelector('.player-next').addEventListener('click', () => next());
    player.querySelector('.player-previous').addEventListener('click', previous);
    shuffleButton.addEventListener('click', () => {
        shuffle = !shuffle;
        shuffleButton.setAttribute('aria-pressed', String(shuffle));
        shuffleButton.title = `Shuffle: ${shuffle ? 'on' : 'off'}`;
        if (shuffle) refillBag();
    });
    repeatButton.addEventListener('click', () => {
        repeat = repeat === 'off' ? 'all' : repeat === 'all' ? 'one' : 'off';
        repeatButton.dataset.mode = repeat;
        repeatButton.title = `Repeat: ${repeat}`;
        const nextMode = repeat === 'off' ? 'Enable repeat all' : repeat === 'all' ? 'Enable repeat one' : 'Disable repeat';
        repeatButton.setAttribute('aria-label', `Repeat: ${repeat}. ${nextMode}`);
    });
    seek.addEventListener('pointerdown', () => { scrubbing = true; });
    const finishScrubbing = () => { scrubbing = false; syncTime(); };
    addEventListener('pointerup', finishScrubbing);
    addEventListener('pointercancel', finishScrubbing);
    addEventListener('blur', finishScrubbing);
    seek.addEventListener('input', () => {
        if (!duration()) return;
        try {
            audio.currentTime = Number(seek.value);
            syncTime();
        } catch {
            announce('Seeking is not available yet. Please wait for the track to load.');
        }
    });
    player.querySelector('.player-close').addEventListener('click', () => {
        generation++;
        audio.pause();
        current = -1;
        audio.removeAttribute('src');
        audio.load();
        player.hidden = true;
        document.body.classList.remove('player-open');
        history = [];
        bag = [];
        announce('');
        syncPlayback();
        if (mediaSession) mediaSession.metadata = null;
        if (returnFocus) returnFocus.focus({preventScroll: true});
    });
    ['play', 'pause', 'ended', 'emptied'].forEach(event => audio.addEventListener(event, syncPlayback));
    ['timeupdate', 'loadedmetadata', 'durationchange', 'emptied'].forEach(event => audio.addEventListener(event, syncTime));
    audio.addEventListener('ended', () => next(true));
    ['loadstart', 'waiting'].forEach(event => audio.addEventListener(event, () => {
        if (!player.hidden && current >= 0) setLoading(true);
    }));
    ['canplay', 'playing', 'pause', 'ended', 'emptied', 'error'].forEach(event => audio.addEventListener(event, () => setLoading(false)));
    audio.addEventListener('playing', () => announce(''));
    audio.addEventListener('error', () => {
        if (!player.hidden) announce('This track could not be loaded. Try again or download the release.');
        syncPlayback();
    });
    if (mediaSession) {
        const handlers = {play, pause: () => { generation++; audio.pause(); }, nexttrack: () => next(), previoustrack: previous,
            seekto: event => { if (duration()) { audio.currentTime = Math.max(0, Math.min(duration(), event.seekTime)); syncTime(); } }};
        Object.entries(handlers).forEach(([action, handler]) => {
            try { mediaSession.setActionHandler(action, handler); } catch { /* Optional browser capability. */ }
        });
    }
})();
