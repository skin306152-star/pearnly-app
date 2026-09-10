/* Draft photos stay with the count until its idempotent save succeeds. */
(function () {
    'use strict';
    async function encode(file) {
        if (!file.size || file.size > 25 * 1024 * 1024) throw new Error('photo_invalid');
        const url = URL.createObjectURL(file);
        try {
            const image = new Image();
            image.src = url;
            await image.decode();
            const scale = Math.min(1280 / image.width, 1280 / image.height, 1);
            const canvas = document.createElement('canvas');
            canvas.width = Math.max(1, Math.round(image.width * scale));
            canvas.height = Math.max(1, Math.round(image.height * scale));
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
            const data = canvas.toDataURL('image/jpeg', 0.8).split(',')[1];
            if (!data || data.length > 1400000) throw new Error('photo_invalid');
            return data;
        } finally {
            URL.revokeObjectURL(url);
        }
    }
    window.PearnlyStocktakePhotos = {
        editor(host, { draft, existing, t, esc }) {
            host.innerHTML = `<p>${esc(t('photos-help'))}</p>
                ${existing ? `<p>${esc(t('photos-saved'))}: ${existing}</p>` : ''}
                <div class="st-toolbar"><button type="button" class="pu-btn pu-btn--secondary" data-photo-pick>${esc(t('upload-photos'))}</button>
                <button type="button" class="pu-btn pu-btn--secondary" data-photo-camera>${esc(t('take-photo'))}</button></div>
                <input type="file" accept="image/*" multiple data-photo-files hidden>
                <input type="file" accept="image/*" capture="environment" data-photo-capture hidden>
                <p data-photo-message role="status"></p><div class="st-photos" data-photo-preview></div>`;
            const message = host.querySelector('[data-photo-message]');
            const draw = () => {
                message.textContent = draft.loading
                    ? t('photos-processing')
                    : draft.error
                      ? t(draft.error)
                      : '';
                host.querySelector('[data-photo-preview]').innerHTML = draft.values
                    .map(
                        (data, i) =>
                            `<figure><img src="data:image/jpeg;base64,${data}" alt="${esc(t('photo'))} ${i + 1}">
                    <button type="button" class="pu-btn pu-btn--secondary" data-photo-remove="${i}" aria-label="${esc(t('remove-photo'))} ${i + 1}">${esc(t('remove-photo'))}</button></figure>`
                    )
                    .join('');
                host.querySelectorAll('[data-photo-remove]').forEach((button) => {
                    button.onclick = () => {
                        if (draft.loading) return;
                        draft.values.splice(Number(button.dataset.photoRemove), 1);
                        draw();
                    };
                });
                host.querySelectorAll('[data-photo-pick],[data-photo-camera]').forEach((b) => {
                    b.disabled = draft.loading || existing + draft.values.length >= 5;
                });
            };
            draft.draw = draw;
            const choose = async (input) => {
                const files = [...input.files];
                input.value = '';
                if (!files.length || draft.loading) return;
                if (existing + draft.values.length + files.length > 5) {
                    draft.error = 'error-photo_limit';
                    draft.draw();
                    return;
                }
                draft.loading = true;
                draft.error = '';
                draft.draw();
                try {
                    const values = [];
                    for (const file of files) values.push(await encode(file));
                    draft.values.push(...values);
                    draft.error = '';
                } catch {
                    draft.error = 'error-photo_invalid';
                } finally {
                    draft.loading = false;
                    draft.draw();
                }
            };
            const files = host.querySelector('[data-photo-files]');
            const capture = host.querySelector('[data-photo-capture]');
            host.querySelector('[data-photo-pick]').onclick = () => files.click();
            host.querySelector('[data-photo-camera]').onclick = () => capture.click();
            files.onchange = () => void choose(files);
            capture.onchange = () => void choose(capture);
            draw();
        },
        async view(host, { api, path, t, esc }) {
            const result = await api(path);
            if (!host.isConnected) return;
            host.querySelector('[data-photo-dialog]')?.remove();
            const dialog = document.createElement('dialog');
            dialog.dataset.photoDialog = '';
            dialog.className = 'st-dialog st-photo-dialog';
            dialog.innerHTML = `<h3>${esc(t('view-photos'))}</h3><button type="button" class="pu-btn pu-btn--secondary">${esc(t('cancel'))}</button>
                <div class="st-photos">${result.photos.map((p) => `<figure><img src="data:image/jpeg;base64,${p.data}" alt="${esc(t('photo'))} ${p.slot}"></figure>`).join('')}</div>`;
            dialog.querySelector('button').onclick = () => dialog.close();
            dialog.onclose = () => dialog.remove();
            host.append(dialog);
            dialog.showModal();
        },
    };
})();
