import { DynamicList } from "../dynamic-list.js";

export function createAudioList(root) {
  return new DynamicList({
    root,
    placeholder: "Paste 1 link YouTube / SoundCloud...",
    bulkPlaceholder: "Paste banyak link audio di sini. Pisahkan dengan enter atau koma.",
    addLabel: "Add Link",
  });
}
