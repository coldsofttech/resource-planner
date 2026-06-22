"use strict";

/* CommentsList  <comments-list>
 *
 * Semantic container for <comment> elements. Managed by <comments-panel>.
 * Provides the empty-state message when no children are present.
 *
 * Usage (managed by CommentsPanel — do not populate manually):
 *   <comments-list></comments-list>
 */
class CommentsList extends HTMLElement {
  showEmpty() {
    this.innerHTML = `<p class="text-muted rp-fs-13 py-3 mb-0">No comments yet. Be the first to comment.</p>`;
  }

  clear() {
    this.innerHTML = "";
  }
}

if (!customElements.get("comment-items")) {
  customElements.define("comment-items", CommentsList);
}
