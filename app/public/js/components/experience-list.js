import { DynamicList } from "../dynamic-list.js";

export function createExperienceList(root) {
  return new DynamicList({
    root,
    placeholder: "Experience / Universe ID...",
    bulkPlaceholder: "Paste banyak experience ID. Pisahkan dengan enter atau koma.",
    addLabel: "Add Experience",
  });
}
