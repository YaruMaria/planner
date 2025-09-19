// Простая анимация для карточек уроков
document.addEventListener('DOMContentLoaded', () => {
    const cards = document.querySelectorAll('.lesson-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease';
            card.style.opacity = '1';
        }, index * 100);
    });
});

// Валидация формы (опционально)
const form = document.querySelector('form');
if (form) {
    form.addEventListener('submit', (e) => {
        const price = document.getElementById('price').value;
        if (price <= 0) {
            alert('Цена должна быть положительной!');
            e.preventDefault();
        }
    });
}
