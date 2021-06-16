var pagItems = document.querySelectorAll('.pagination__item');

for (var i = 0; i < pagItems.length; i++) {
  var counter = i + 1;
  var string = "Page " + counter;

  if (pagItems[i].getAttribute('aria-current')) {
    string = "Page " + counter + ", Current Page";
  }

  pagItems[i].setAttribute('aria-label', string);
}