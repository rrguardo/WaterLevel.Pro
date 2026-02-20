// Triggers a product page-view conversion event when GA is available.
if (typeof gtag === 'function') {
  gtag('event', 'conversion_event_page_view', {});
}
