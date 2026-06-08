import { PrimaryButton } from "./primary-button.js";

/* EngineButton  <engine-button>
 * Extends PrimaryButton with variant "rp-btn-engine". Same attributes.
 * Typical use: triggering processing/run/engine actions.
 * See primary-button.js for full attribute / API documentation. */
class EngineButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-engine";
  }
}

customElements.define("engine-button", EngineButton);
