(function () {
    class MascotSoundController {
        constructor(options) {
            this.basePath = options.basePath;
            // 音频缓存版本 · 音频文件被 immutable 30d 缓存(浏览器 + Cloudflare)·
            // 换音频后 bump 这个数,URL 变 = 强制取新文件
            this.audioVersion = '2';
            this.storageKey = 'pearnly_mascot_muted';
            this.mobileNoSound = window.matchMedia('(max-width: 720px)').matches;
            this.muted = localStorage.getItem(this.storageKey) === '1';
            // 自然音量 · 完全交给用户的系统音量控制(像普通媒体一样随音量变大变小)
            this.volume = 1.0;
            this.players = new Map();
            this.files = {
                tap: 'tap.wav',
                success: 'success.wav',
                bell: 'bell.wav',
                pop: 'pop.wav',
                watering: 'watering.mp3',
                pour: 'pour.mp3',
                meow: 'meow.mp3',
                computer: 'computer.mp3',
            };
        }

        setMuted(nextMuted) {
            this.muted = nextMuted;
            localStorage.setItem(this.storageKey, nextMuted ? '1' : '0');
        }

        play(name) {
            if (this.muted || this.mobileNoSound) return;
            const player = this.playerFor(name);
            if (!player) {
                this.tone(name);
                return;
            }
            player.currentTime = 0;
            player.volume = this.volume;
            player.play().catch(() => this.tone(name));
        }

        playerFor(name) {
            const file = this.files[name];
            if (!file) return null;
            if (!this.players.has(name)) {
                const audio = new Audio(`${this.basePath}${file}?v=${this.audioVersion}`);
                audio.preload = 'none';
                this.players.set(name, audio);
            }
            return this.players.get(name);
        }

        tone(name) {
            if (!window.AudioContext && !window.webkitAudioContext) return;
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            const ctx = new AudioContext();
            // meow.wav 缺失时的合成兜底:升降调 + 带通共振 ≈ 卡通猫叫(放真 meow.wav 即用文件)
            if (name === 'meow') {
                this.meow(ctx);
                return;
            }
            const gain = ctx.createGain();
            const osc = ctx.createOscillator();
            const notes = {
                tap: [520, 0.07],
                success: [660, 0.13],
                bell: [840, 0.12],
                pop: [580, 0.08],
            };
            const [freq, dur] = notes[name] || notes.tap;
            osc.type = name === 'bell' ? 'sine' : 'triangle';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(this.volume * 0.7, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + dur);
        }

        meow(ctx) {
            const now = ctx.currentTime;
            const osc = ctx.createOscillator();
            const filter = ctx.createBiquadFilter();
            const gain = ctx.createGain();
            osc.type = 'sawtooth';
            // 音高包络:"喵"先升后降
            osc.frequency.setValueAtTime(600, now);
            osc.frequency.linearRampToValueAtTime(940, now + 0.12);
            osc.frequency.linearRampToValueAtTime(480, now + 0.5);
            filter.type = 'bandpass';
            filter.frequency.value = 1100;
            filter.Q.value = 6;
            gain.gain.setValueAtTime(0.0001, now);
            gain.gain.exponentialRampToValueAtTime(this.volume * 0.6, now + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.55);
            osc.connect(filter);
            filter.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now);
            osc.stop(now + 0.6);
        }
    }

    class MascotInteractionLayer {
        constructor(panel, scene, sound) {
            this.panel = panel;
            this.scene = scene;
            this.sound = sound;
            this.reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            // 背景图是整图 · 猫各部位用透明热区叠在对应位置(点击=音效+火花+浮字)
            this.hotspots = [
                {
                    id: 'logo',
                    label: 'Pearnly',
                    sound: 'meow',
                    marks: ['heart', 'star', 'heart'],
                },
                {
                    id: 'face',
                    label: 'Pearl the cat',
                    sound: 'meow',
                    marks: ['heart', 'heart'],
                    sayKey: 'sayFace',
                },
                {
                    id: 'paw',
                    label: 'High five',
                    sound: 'pop',
                    marks: ['star', 'heart', 'star'],
                    sayKey: 'sayPaw',
                },
                {
                    id: 'bell',
                    label: 'Bell',
                    sound: 'bell',
                    marks: ['star'],
                    sayKey: 'sayBell',
                },
                {
                    id: 'laptop',
                    label: 'Laptop',
                    sound: 'computer',
                    marks: ['star', 'star'],
                    sayKey: 'sayLaptop',
                    effect: 'glow',
                },
                {
                    id: 'mugr',
                    label: 'Coffee',
                    sound: 'pour',
                    marks: ['drop', 'star'],
                    sayKey: 'sayMug',
                    effect: 'steam',
                },
                {
                    id: 'bubble',
                    label: 'Say hi',
                    sound: 'tap',
                    marks: ['star', 'heart'],
                    sayKey: 'sayBubble',
                },
                {
                    id: 'plant',
                    label: 'Plant',
                    sound: 'watering',
                    marks: ['drop', 'star'],
                    sayKey: 'sayPlant',
                    effect: 'water',
                },
                {
                    id: 'checklist',
                    label: 'Checklist',
                    sound: 'success',
                    marks: ['star', 'star', 'star'],
                    sayKey: 'sayCheck',
                },
            ];
            // 引言现在是透明文字浮在背景面板上 · 不绑卡片悬浮动画(否则悬停露出残缺阴影)
            this.cards = [];
        }

        mount() {
            this.layer = document.createElement('div');
            this.layer.className = 'mascot-interaction-layer';
            this.effectLayer = document.createElement('div');
            this.effectLayer.className = 'mascot-effect-layer';
            this.panel.append(this.layer, this.effectLayer);
            this.hotspots.forEach((hotspot) => this.addHotspot(hotspot));
            this.cards.forEach((card) => this.bindCard(card));
        }

        addHotspot(hotspot) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `mascot-hotspot ${hotspot.id}-hotspot`;
            button.setAttribute('aria-label', hotspot.label);
            button.addEventListener('click', () => this.activate(hotspot, button, true));
            button.addEventListener('mouseenter', () => this.activate(hotspot, button, false));
            this.layer.appendChild(button);
        }

        bindCard(card) {
            const el = this.panel.querySelector(card.sel);
            if (!el) return;
            el.style.cursor = 'pointer';
            el.addEventListener('click', () => this.activateCard(card, el, true));
            el.addEventListener('mouseenter', () => this.activateCard(card, el, false));
        }

        activate(hotspot, button, click) {
            const rect = button.getBoundingClientRect();
            if (click) {
                this.sound.play(hotspot.sound);
                if (!this.reduceMotion) {
                    this.burst(rect, hotspot.marks);
                    if (hotspot.effect) this.themedEffect(rect, hotspot.effect);
                    const text = window.PearnlyMsg ? window.PearnlyMsg(hotspot.sayKey) : '';
                    if (text) this.say(rect, text);
                }
                return;
            }
            // 悬停:单颗火花预览,不出声
            if (!this.reduceMotion) this.burst(rect, [hotspot.marks[0]]);
        }

        // 舞台用 transform 缩放 · getBoundingClientRect 是缩放后屏幕 px ·
        // 特效层在缩放容器内(本地 px)· 故 delta 需除以缩放比 · 否则放大缩小时位置漂移
        stageScale(base) {
            return base.width / this.panel.offsetWidth || 1;
        }

        say(rect, text) {
            const base = this.panel.getBoundingClientRect();
            const scale = this.stageScale(base);
            const label = document.createElement('span');
            label.className = 'mascot-say';
            label.textContent = text;
            label.style.left = `${(rect.left - base.left + rect.width / 2) / scale}px`;
            label.style.top = `${(rect.top - base.top) / scale - 6}px`;
            this.effectLayer.appendChild(label);
            window.setTimeout(() => label.remove(), 1100);
        }

        // 主题特效: water=花盆浇水落下 · steam=水杯热气上升 · glow=电脑屏幕亮起
        themedEffect(rect, type) {
            const base = this.panel.getBoundingClientRect();
            const scale = this.stageScale(base);
            const cx = (rect.left - base.left + rect.width / 2) / scale;
            const cy = (rect.top - base.top + rect.height / 2) / scale;
            if (type === 'glow') {
                const el = document.createElement('span');
                el.className = 'mascot-glow-fx';
                el.style.left = `${cx}px`;
                el.style.top = `${cy}px`;
                this.effectLayer.appendChild(el);
                window.setTimeout(() => el.remove(), 820);
                return;
            }
            const count = type === 'water' ? 5 : 3;
            for (let i = 0; i < count; i += 1) {
                const el = document.createElement('span');
                el.className = type === 'water' ? 'mascot-water' : 'mascot-steam';
                const dx = (i - (count - 1) / 2) * (type === 'water' ? 11 : 13);
                el.style.left = `${cx + dx}px`;
                el.style.top = `${cy + (type === 'water' ? -14 : -4)}px`;
                el.style.animationDelay = `${i * (type === 'water' ? 70 : 120)}ms`;
                this.effectLayer.appendChild(el);
                window.setTimeout(() => el.remove(), 1320 + i * 130);
            }
        }

        activateCard(card, el, click) {
            if (click) {
                this.sound.play(card.sound);
                this.restartClass(el, card.active);
                if (!this.reduceMotion) this.burst(el.getBoundingClientRect(), card.marks);
                return;
            }
            this.restartClass(el, 'card-hover', 340);
            if (!this.reduceMotion) this.burst(el.getBoundingClientRect(), [card.marks[0]]);
        }

        restartClass(target, className, duration) {
            target.classList.remove(className);
            window.requestAnimationFrame(() => {
                target.classList.add(className);
                window.setTimeout(() => target.classList.remove(className), duration || 760);
            });
        }

        burst(rect, marks) {
            const base = this.panel.getBoundingClientRect();
            const scale = this.stageScale(base);
            const cx = (rect.left - base.left + rect.width / 2) / scale;
            const cy = (rect.top - base.top + rect.height / 2) / scale;
            marks.forEach((kind, index) => {
                const mark = document.createElement('span');
                mark.className = `mascot-effect ${kind}`;
                mark.textContent = this.symbolFor(kind);
                const offset = index - (marks.length - 1) / 2;
                mark.style.left = `${cx + offset * 18}px`;
                mark.style.top = `${cy + (index % 2) * 6}px`;
                mark.style.setProperty('--dx', `${offset * 18}px`);
                mark.style.setProperty('--dy', `${-28 - index * 7}px`);
                this.effectLayer.appendChild(mark);
                window.setTimeout(() => mark.remove(), 820);
            });
        }

        symbolFor(kind) {
            if (kind === 'drop') return '•';
            if (kind === 'heart') return '♡';
            if (kind === 'glow') return '';
            return '✦';
        }
    }

    class PearnlyMascotScene {
        constructor() {
            this.panel = document.querySelector('.brand-panel');
            this.sound = new MascotSoundController({
                basePath: '/static/landing/sounds/mascot/',
            });
        }

        mount() {
            if (!this.panel) return;
            this.layer = new MascotInteractionLayer(this.panel, this, this.sound);
            this.layer.mount();
        }
    }

    window.PearnlyMascotScene = PearnlyMascotScene;
    window.MascotInteractionLayer = MascotInteractionLayer;
    window.MascotSoundController = MascotSoundController;
    new PearnlyMascotScene().mount();
})();
