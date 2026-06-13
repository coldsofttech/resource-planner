/* AccordionBody  <accordion-body>
 * Declarative container for the collapsible body content of <accordion-panel>.
 * Its child nodes are captured once by <accordion-panel> on connect and moved
 * into the rendered body slot.
 * Do not use standalone — must be a direct child of <accordion-panel>. */
class AccordionBody extends HTMLElement {}

customElements.define("accordion-body", AccordionBody);
