(function () {
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function suppressThinkingMarkup(source) {
    let out = String(source || "");
    const openThink = "<" + "think>";
    const closeThink = "</" + "think>";
    const blockPatterns = [
      /<redacted_thinking\b[^>]*>[\s\S]*?<\/redacted_thinking>/gi,
      /<thinking\b[^>]*>[\s\S]*?<\/thinking>/gi,
      /<reasoning\b[^>]*>[\s\S]*?<\/reasoning>/gi,
      new RegExp(openThink.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "[\\s\\S]*?" + closeThink.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi"),
      /<redacted_thinking\b[^>]*>[\s\S]*/gi,
      /<thinking\b[^>]*>[\s\S]*/gi,
      /<reasoning\b[^>]*>[\s\S]*/gi,
      new RegExp(openThink.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "[\\s\\S]*", "gi"),
    ];
    const fragPatterns = [
      /<\/?redacted_thinking\b[^>]*>/gi,
      /<\/?thinking\b[^>]*>/gi,
      /<\/?reasoning\b[^>]*>/gi,
    ];
    for (let pass = 0; pass < 4; pass += 1) {
      const prev = out;
      blockPatterns.forEach((re) => {
        out = out.replace(re, "");
      });
      fragPatterns.forEach((re) => {
        out = out.replace(re, "");
      });
      if (out === prev) break;
    }
    return out.replace(/\n{3,}/g, "\n\n").trim();
  }

  function inlineMarkdown(text) {
    let s = escapeHtml(text);
    s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, (_m, label, url) => {
      const safeUrl = escapeHtml(url);
      return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer" class="asst-md-link">${label}</a>`;
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

  function renderAssistantMarkdown(source) {
    const cleaned = demoteTableLines(suppressThinkingMarkup(source));
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
      } else if (/redacted_thinking|<\/?thinking/i.test(line)) {
        continue;
      } else {
        closeList();
        parts.push(`<p class="asst-md-p">${inlineMarkdown(line)}</p>`);
      }
    }
    closeList();
    return parts.join("");
  }

  function looksLikeMarkdown(text) {
    const s = suppressThinkingMarkup(text);
    if (/^#{1,3}\s/m.test(s)) return true;
    if (/^\s*[-*]\s+/m.test(s)) return true;
    if (/^\s*\d+\.\s+/m.test(s)) return true;
    if (/\*\*.+\*\*/s.test(s)) return true;
    if (/`[^`]+`/.test(s)) return true;
    if (/\[[^\]]+\]\(https?:\/\//.test(s)) return true;
    return false;
  }

  function setAssistantMessageBody(el, role, text) {
    if (!el) return;
    const visible =
      role === "assistant" ? suppressThinkingMarkup(text) : String(text || "");
    el.parentElement?.querySelector(".assistant-thinking")?.remove();

    if (role === "assistant" && looksLikeMarkdown(visible)) {
      el.classList.add("assistant-markdown");
      el.innerHTML = renderAssistantMarkdown(visible);
    } else {
      el.classList.remove("assistant-markdown");
      el.textContent = visible;
    }
  }

  window.suppressThinkingMarkup = suppressThinkingMarkup;
  window.renderAssistantMarkdown = renderAssistantMarkdown;
  window.looksLikeMarkdown = looksLikeMarkdown;
  window.setAssistantMessageBody = setAssistantMessageBody;
})();
