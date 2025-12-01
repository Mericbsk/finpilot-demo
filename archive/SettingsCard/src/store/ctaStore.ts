import { create } from "zustand";
import type { CtaContract, PrimaryCtaStatus, SecondaryCtaStatus } from "../types/cta";
import { ctaContract } from "../data/ctaConfig";

interface CtaStoreState {
  contract: CtaContract;
  primaryStatus: PrimaryCtaStatus;
  secondaryStatus: SecondaryCtaStatus;
  triggerPrimary: () => void;
  setPrimaryStatus: (status: PrimaryCtaStatus) => void;
  setSecondaryStatus: (status: SecondaryCtaStatus) => void;
}

let scanTimer: number | undefined;

export const useCtaStore = create<CtaStoreState>((set) => ({
  contract: ctaContract,
  primaryStatus: ctaContract.ana.durum,
  secondaryStatus: ctaContract.ikincil.durum,
  setPrimaryStatus: (status) => set({ primaryStatus: status }),
  setSecondaryStatus: (status) => set({ secondaryStatus: status }),
  triggerPrimary: () => {
    set((state) => {
      if (state.primaryStatus === "loading") {
        return state;
      }
      return {
        primaryStatus: "loading",
        contract: state.contract
      };
    });

    if (typeof window !== "undefined") {
      if (scanTimer) {
        window.clearTimeout(scanTimer);
      }
      scanTimer = window.setTimeout(() => {
        set((state) => ({
          primaryStatus: "completed",
          contract: state.contract
        }));
      }, 2600);
    }
  }
}));
