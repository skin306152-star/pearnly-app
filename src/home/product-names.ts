export interface ProductNames {
    display?: string | null;
    display_name?: string | null;
    name_th?: string | null;
    name_en?: string | null;
    name_zh?: string | null;
    th?: string | null;
    en?: string | null;
    zh?: string | null;
}

export function productDisplayName(value: ProductNames, missing = '—'): string {
    const ready = String(value.display_name || value.display || '').trim();
    if (ready) return ready;
    const seen = new Set<string>();
    const names = [value.name_th ?? value.th, value.name_en ?? value.en, value.name_zh ?? value.zh]
        .map((name) => String(name || '').trim())
        .filter((name) => {
            const key = name.toLocaleLowerCase();
            if (!name || seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    return names.join(' / ') || missing;
}
