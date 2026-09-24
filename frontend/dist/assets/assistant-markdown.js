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
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_m, label, url) => {
      const safeUrl = escapeHtml(url);
      const safeLabel = label;
      return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="asst-md-link">${safeLabel}</a>`;
    });
    s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
    s = s.replace(/`([^`]+)`/g, "<code class=\"asst-md-code\">$1</code>");
    return s;
  }

  function demoteTableLines(source) {
    const lines = String(source || "").split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      const next = lines[i + 1] || "";
      if (line.includes("|") && /^\s*\|?\s*:?-{2,}/.test(next)) {
        i += 2;
        while (i < lines.length && lines[i].includes("|")) {
          const cells = lines[i]
            .split("|")
            .map((c) => c.trim())
            .filter(Boolean);
          if (cells.length) out.push(`- ${cells.join(" · ")}`);
          i += 1;
        }
        continue;
      }
      if (/^\s*\|/.test(line)) {
        const cells = line
          .split("|")
          .map((c) => c.trim())
          .filter(Boolean);
        if (cells.length) out.push(`- ${cells.join(" · ")}`);
        i += 1;
        continue;
      }
      out.push(line);
      i += 1;
    }
    return out.join("\n");
  }

  function extractThinking(source) {
    let visible = String(source || "");
    const thinkingParts = [];
    const patterns = [
      /<think>[\s\S]*?<\/redacted_thinking>/gi,
      /<thinking>[\s\S]*?<\/thinking>/gi,
      /<reasoning>[\s\S]*?<\/reasoning>/gi,
    ];
    patterns.forEach((re) => {
      visible = visible.replace(re, (block) => {
        thinkingParts.push(block.replace(/<\/?[^>]+>/g, "").trim());
        return "";
      });
    });
    return { visible: visible.trim(), thinking: thinkingParts.filter(Boolean).join("\n\n") };
  }

  function renderAssistantMarkdown(source) {
    const cleaned = demoteTableLines(source);
    const lines = cleaned.split("\n");
    const parts = [];
    let inList = false;
    let listOrdered = false;

    const closeList = () => {
      if (inList) {
        parts.push(listOrdered ? "</ol>" : "</ul>");
        inList = false;
        listOrdered = false;
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
      } else if (/^\d+\.\s+/.test(line)) {
        if (!inList || !listOrdered) {
          closeList();
          parts.push('<ol class="asst-md-ol">');
          inList = true;
          listOrdered = true;
        }
        parts.push(`<li class="asst-md-li">${inlineMarkdown(line.replace(/^\d+\.\s+/, ""))}</li>`);
      } else if (/^[-*]\s+/.test(line)) {
        if (!inList || listOrdered) {
          closeList();
          parts.push('<ul class="asst-md-ul">');
          inList = true;
          listOrdered = false;
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
    if (/^\s*\d+\.\s+/m.test(s)) return true;
    if (/\*\*.+\*\*/s.test(s)) return true;
    if (/`[^`]+`/.test(s)) return true;
    if (/\[[^\]]+\]\(https?:\/\//.test(s)) return true;
    return false;
  }

  function renderThinkingFold(thinkingText) {
    if (!thinkingText || !thinkingText.trim()) return null;
    const details = document.createElement("details");
    details.className = "assistant-thinking";
    const summary = document.createElement("summary");
    summary.textContent = "Model reasoning (collapsed)";
    const body = document.createElement("div");
    body.className = "assistant-thinking-body";
    body.textContent = thinkingText.trim();
    details.appendChild(summary);
    details.appendChild(body);
    return details;
  }

  function setAssistantMessageBody(el, role, text, options) {
    if (!el) return;
    const opts = options || {};
    let visible = text;
    let thinking = opts.thinkingTrace || "";
    if (role === "assistant" && !thinking) {
      const split = extractThinking(text);
      visible = split.visible || text;
      thinking = split.thinking;
    }
    const parent = el.parentElement;
    parent?.querySelector(".assistant-thinking")?.remove();

    if (role === "assistant" && looksLikeMarkdown(visible)) {
      el.classList.add("assistant-markdown");
      el.innerHTML = renderAssistantMarkdown(visible);
    } else {
      el.classList.remove("assistant-markdown");
      el.textContent = visible;
    }
    const fold = renderThinkingFold(thinking);
    if (fold && parent) {
      parent.insertBefore(fold, el.nextSibling);
    }
  }

  window.renderAssistantMarkdown = renderAssistantMarkdown;
  window.looksLikeMarkdown = looksLikeMarkdown;
  window.setAssistantMessageBody = setAssistantMessageBody;
})();
