import { create } from 'zustand';

interface GraphModalStore {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
}

export const useGraphModal = create<GraphModalStore>((set) => ({
  isOpen: false,
  openModal: () => set({ isOpen: true }),
  closeModal: () => set({ isOpen: false }),
}));
