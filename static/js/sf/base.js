"use strict";
// Account for both dimensions when a background covers a tall release section.
document.querySelectorAll('[data-cover-image]').forEach(picture => {
    const img = picture.querySelector('img');
    const source = picture.querySelector('source');
    const ratio = Number(img.getAttribute('width')) / Number(img.getAttribute('height'));
    const resize = () => {
        const box = img.getBoundingClientRect();
        const sizes = `${Math.ceil(Math.max(box.width, box.height * ratio))}px`;
        if (source.sizes !== sizes) source.sizes = sizes;
    };
    resize();
    new ResizeObserver(resize).observe(img);
});
const menu = document.querySelector('.site-menu');
if (menu) {
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && menu.open) {
            menu.open = false;
            menu.querySelector('summary').focus();
        }
    });
    document.addEventListener('click', event => {
        if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => { menu.open = false; }));
}
