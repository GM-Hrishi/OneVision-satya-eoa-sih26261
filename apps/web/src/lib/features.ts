// Feature switches (prompt 7.10). The reuse graph needs a cross-case fingerprint index that neither main nor the
// backend branch provides, so it is off everywhere except development with NEXT_PUBLIC_UI_FIXTURES=1.
import { uiFixtures } from "./fixtures";

export const features = {
  get reuseGraph(): boolean {
    return uiFixtures();
  },
};
