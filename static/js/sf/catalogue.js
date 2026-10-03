"use strict";
const search = document.querySelector('#release-search');
if (search) {
    const cards = [...document.querySelectorAll('[data-search]')];
    const count = document.querySelector('#release-count');
    const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    cards.forEach(card => { card.searchText = normalize(card.dataset.search); });
    const update = () => {
        const query = normalize(search.value.trim());
        let visible = 0;
        cards.forEach(card => {
            card.hidden = !card.searchText.includes(query);
            if (!card.hidden) visible++;
        });
        count.textContent = `${visible} ${visible === 1 ? 'release' : 'releases'}`;
        document.querySelector('#release-empty').hidden = visible !== 0;
    };
    document.querySelector('[data-search-controls]').hidden = false;
    search.addEventListener('input', update);
    update();
}
