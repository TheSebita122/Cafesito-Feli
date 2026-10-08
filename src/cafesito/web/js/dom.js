export const $ = (selector, root = document) => root.querySelector(selector);

export function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  const { className, text, attrs = {} } = options;
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  Object.entries(attrs).forEach(([name, value]) => node.setAttribute(name, value));
  [].concat(children).forEach((child) => {
    if (child) node.append(child);
  });
  return node;
}

export function showMessage(container, message) {
  container.textContent = message;
  container.hidden = false;
}

export function hideMessage(container) {
  container.textContent = "";
  container.hidden = true;
}

export function fillSelect(select, options, selected) {
  select.replaceChildren(
    ...options.map(({ value, label }) => {
      const option = el("option", { text: label, attrs: { value: String(value) } });
      if (selected !== undefined && String(selected) === String(value)) option.selected = true;
      return option;
    }),
  );
}

export function setBusy(button, busy, busyLabel) {
  if (busy) {
    button.dataset.label = button.textContent;
    button.textContent = busyLabel;
  } else if (button.dataset.label) {
    button.textContent = button.dataset.label;
  }
  button.disabled = busy;
}
