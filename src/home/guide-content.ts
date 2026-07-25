// ============================================================
// 使用教程 · 内容加载(Express 推送手册)
// 正文不进 JS bundle:124 章中泰双语几百 KB,塞进 main.js 会拖慢所有页面的首屏,
// 而教程是低频入口。改成按篇 JSON 懒加载,随 dist 一起部署(新增 static 根文件
// 不会被 webhook 拾取,dist 子目录实测可靠)。
// 指纹沿用页面上 main.js 的 ?v —— 每次发版自动破缓存,不用另记一套版本号。
// ============================================================

export type Lang = 'zh' | 'th';

export interface Bilingual {
    zh: string;
    th: string;
}

export interface GuideStep {
    text: Bilingual;
    // 配图基名 · 实际取 /static/dist/guide-shots/<shot>.<lang>.png
    shot?: string;
    caption?: Bilingual;
}

export interface GuideNote {
    kind: 'info' | 'warn';
    text: Bilingual;
}

export interface GuideChapter {
    id: string;
    title: Bilingual;
    intro: Bilingual;
    steps: GuideStep[];
    notes: GuideNote[];
}

export interface SectionMeta {
    id: string;
    title: Bilingual;
    // 清单定稿的章数 · 与已完工章数一起显示,读者看得到这篇还剩多少
    planned: number;
    // 已完工章数 · 由构建期数各篇 chapters 写进 dist 的 index.json(源 index.json 不写:
    // 手写必然漂)。首页七张卡只要这七个数字,不该为此把全书正文拉下来。
    done: number;
}

export interface BookIndex {
    book: Bilingual;
    sections: SectionMeta[];
}

const BASE = '/static/dist/guide-content/';

// 教程页与深链映射两边都要转义/取词条,提到这里共用(此前各写一份逐字相同的实现)。
export function esc(s: string): string {
    return s.replace(
        /[&<>"']/g,
        (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string
    );
}

export function T(key: string): string {
    const fn = (window as unknown as { t?: (k: string) => string }).t;
    const v = typeof fn === 'function' ? fn(key) : '';
    return v || key;
}

function fingerprint(): string {
    const el = document.querySelector<HTMLScriptElement>('script[src*="/dist/main.js"]');
    const m = el && el.src.match(/[?&]v=([^&]+)/);
    return m ? m[1] : '';
}

const url = (name: string): string => `${BASE}${name}.json?v=${fingerprint()}`;

let index: BookIndex | null = null;
let indexPending: Promise<BookIndex | null> | null = null;
const sections = new Map<string, GuideChapter[]>();

async function fetchIndex(): Promise<BookIndex | null> {
    try {
        const r = await fetch(url('index'));
        if (r.ok) index = (await r.json()) as BookIndex;
    } catch {
        /* 目录取不到就当没有:页面回落到手册名占位,不弹错 */
    }
    indexPending = null;
    return index;
}

// 进教程页时侧栏点击与路由派发会各叫一次(手机端还多一次)—— 缓存要连在途请求一起认,
// 只认结果的话同一份目录会被并发拉好几遍。
export function loadIndex(): Promise<BookIndex | null> {
    if (index) return Promise.resolve(index);
    if (!indexPending) indexPending = fetchIndex();
    return indexPending;
}

// 已完工章节:某篇还没开工时文件不存在,404 按空篇处理,不当故障。
export async function loadSection(id: string): Promise<GuideChapter[]> {
    const hit = sections.get(id);
    if (hit) return hit;
    let list: GuideChapter[] = [];
    try {
        const r = await fetch(url(id));
        if (r.ok) {
            const data = (await r.json()) as { chapters?: GuideChapter[] };
            if (Array.isArray(data.chapters)) list = data.chapters;
        }
    } catch {
        /* 网络失败按空篇渲染,页面给的是「编写中」而不是错误弹窗 */
    }
    sections.set(id, list);
    return list;
}

export function loadedIndex(): BookIndex | null {
    return index;
}

export function loadedSection(id: string): GuideChapter[] | undefined {
    return sections.get(id);
}

export function findLoadedChapter(id: string): GuideChapter | null {
    for (const list of sections.values()) {
        const hit = list.find((c) => c.id === id);
        if (hit) return hit;
    }
    return null;
}

// 深链要能直达任意章,而章属于哪一篇只有 index 知道 → 顺序探测已开工的篇。
export async function findChapterAcrossBook(
    id: string
): Promise<{ sectionId: string; chapter: GuideChapter } | null> {
    const idx = await loadIndex();
    if (!idx) return null;
    for (const s of idx.sections) {
        const list = await loadSection(s.id);
        const hit = list.find((c) => c.id === id);
        if (hit) return { sectionId: s.id, chapter: hit };
    }
    return null;
}
