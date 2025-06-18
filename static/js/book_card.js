function expandBookCard(bookId) {
    const bookCard = document.getElementById(`book-card_${bookId}`);
    expanded = bookCard.getAttribute('expanded') === 'true';
    bookCard.setAttribute('expanded', !expanded);
}
