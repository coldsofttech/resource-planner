/* AccordionHeader  <accordion-header>
 * Declarative container for custom header content inside <accordion-panel>.
 * Its child nodes are captured once by <accordion-panel> on connect and placed
 * after the chevron in the rendered header region.
 * Do not use standalone — must be a direct child of <accordion-panel>. */
class AccordionHeader extends HTMLElement {}

customElements.define("accordion-header", AccordionHeader);
