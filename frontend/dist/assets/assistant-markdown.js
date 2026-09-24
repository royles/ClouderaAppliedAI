(function () {
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function inlineMarkdown(text) {
    let s = escapeHtml(text);
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
    s = s.replace(/`([^`]+)`/g, "<code class=\"asst-md-code\">$1</code>");
    return s;
  }

  function renderAssistantMarkdown(source) {
    const lines = String(source || "").split("\n");
    const parts = [];
    let inList = false;

    const closeList = () => {
      if (inList) {
        parts.push("</ul>");
        inList = false;
      }
    };

    for (const raw of lines) {
      const line = raw.replace(/\r$/, "");
      if (/^###\s+/.test(line)) {
        closeList();
        parts.push(`<h4 class="asst-md-h">${inlineMarkdown(line.replace(/^###\s+/, ""))}</h4>`);
      } else if (/^##\s+/.test(line)) {
        closeList();
        parts.push(`<h3 class="asst-md-h">${inlineMarkdown(line.replace(/^##\s+/, ""))}</h3>`);
      } else if (/^#\s+/.test(line)) {
        closeList();
        parts.push(`<h3 class="asst-md-h">${inlineMarkdown(line.replace(/^#\s+/, ""))}</h3>`);
      } else if (/^[-*]\s+/.test(line)) {
        if (!inList) {
          parts.push('<ul class="asst-md-ul">');
          inList = true;
        }
        parts.push(`<li class="asst-md-li">${inlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>`);
      } else if (line.trim() === "") {
        closeList();
      } else {
        closeList();
        parts.push(`<p class="asst-md-p">${inlineMarkdown(line)}</p>`);
      }
    }
    closeList();
    return parts.join("");
  }

  function looksLikeMarkdown(text) {
    const s = String(text || "");
    if (/^#{1,3}\s/m.test(s)) return true;
    if (/^\s*[-*]\s+/m.test(s)) return true;
    if (/\*\*.+\*\*/s.test(s)) return true;
    if (/`[^`]+`/.test(s)) return true;
    return false;
  }

  function setAssistantMessageBody(el, role, text) {
    if (!el) return;
    if (role === "assistant" && looksLikeMarkdown(text)) {
      el.classList.add("assistant-markdown");
      el.innerHTML = renderAssistantMarkdown(text);
    } else {
      el.classList.remove("assistant-markdown");
      el.textContent = text;
    }
  }

  window.renderAssistantMarkdown = renderAssistantMarkdown;
  window.looksLikeMarkdown = looksLikeMarkdown;
  window.setAssistantMessageBody = setAssistantMessageBody;
})();
