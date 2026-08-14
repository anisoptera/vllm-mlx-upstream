"use strict";

(() => {
  const language = document.documentElement.lang.split("-")[0];
  const messages = {
    en: {
      menu: "Open navigation",
      search: "Open search",
      unavailable: "Translation unavailable; opens the language homepage",
      home: "home",
    },
    es: {
      menu: "Abrir navegación",
      search: "Abrir búsqueda",
      unavailable: "Traducción no disponible; abre el inicio del idioma",
      home: "inicio",
    },
    fr: {
      menu: "Ouvrir la navigation",
      search: "Ouvrir la recherche",
      unavailable: "Traduction indisponible ; ouvre l’accueil de la langue",
      home: "accueil",
    },
    zh: {
      menu: "打开导航",
      search: "打开搜索",
      unavailable: "暂无翻译；打开该语言首页",
      home: "首页",
    },
  }[language] || {
    menu: "Open navigation",
    search: "Open search",
    unavailable: "Translation unavailable; opens the language homepage",
    home: "home",
  };
  const sitePrefix = "/vllm-mlx/";

  const languageForPath = (path) => {
    const relative = path.startsWith(sitePrefix)
      ? path.slice(sitePrefix.length)
      : path.replace(/^\/+/, "");
    const match = relative.match(/^(es|fr|zh)(?:\/|$)/);
    return match ? match[1] : "en";
  };

  const languageHome = (locale) =>
    locale === "en" ? sitePrefix : `${sitePrefix}${locale}/`;

  if (document.querySelector(".vllm-hero")) {
    document
      .querySelector('article.md-content__inner > a[rel="edit"]')
      ?.remove();
  }

  function enhanceToggle(
    inputId,
    labelSelector,
    accessibleName,
    targetSelector,
    targetId,
  ) {
    const input = document.getElementById(inputId);
    const label = document.querySelector(labelSelector);
    const target = document.querySelector(targetSelector);
    if (!input || !label || !target) return;

    target.id = targetId;
    label.setAttribute("role", "button");
    label.setAttribute("tabindex", "0");
    label.setAttribute("aria-label", accessibleName);
    label.setAttribute("aria-controls", targetId);

    const synchronize = () => {
      label.setAttribute("aria-expanded", String(input.checked));
    };
    label.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      input.click();
    });
    input.addEventListener("change", synchronize);
    synchronize();
  }

  enhanceToggle(
    "__drawer",
    'label.md-header__button[for="__drawer"]',
    messages.menu,
    ".md-sidebar--primary",
    "primary-navigation",
  );
  enhanceToggle(
    "__search",
    'label.md-header__button[for="__search"]',
    messages.search,
    ".md-search",
    "site-search",
  );

  document
    .querySelectorAll('[data-md-component="palette"] label.md-header__button')
    .forEach((label) => {
      const input = document.getElementById(label.htmlFor);
      if (!input) return;
      label.setAttribute("role", "button");
      label.setAttribute("tabindex", "0");
      label.setAttribute(
        "aria-label",
        label.title || input.getAttribute("aria-label") || "Change color scheme",
      );
      label.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        input.click();
      });
    });

  document.querySelectorAll(".md-select").forEach((selector) => {
    const button = selector.querySelector("button");
    const list = selector.querySelector("ul");
    if (!button || !list) return;

    button.setAttribute("aria-haspopup", "menu");
    button.setAttribute("aria-expanded", "false");
    list.setAttribute("role", "menu");
    list.querySelectorAll("a").forEach((link) => {
      link.setAttribute("role", "menuitem");
      if (link.hreflang === language) {
        link.setAttribute("aria-current", "page");
      } else {
        const target = new URL(link.href, window.location.href);
        const currentIsHome = window.location.pathname === languageHome(language);
        const targetIsHome = target.pathname === languageHome(link.hreflang);
        if (!currentIsHome && targetIsHome) {
          link.classList.add("md-select__link--unavailable");
          link.title = messages.unavailable;
          link.setAttribute(
            "aria-label",
            `${link.textContent.trim()}: ${messages.unavailable}`,
          );
          const note = document.createElement("span");
          note.className = "md-select__note";
          note.textContent = messages.home;
          link.append(note);
        }
      }
    });

    const open = () => button.setAttribute("aria-expanded", "true");
    const close = () => button.setAttribute("aria-expanded", "false");
    selector.addEventListener("mouseenter", open);
    selector.addEventListener("mouseleave", close);
    selector.addEventListener("focusin", open);
    selector.addEventListener("focusout", (event) => {
      if (!selector.contains(event.relatedTarget)) close();
    });
  });

  const symbolFilter = document.getElementById("api-symbol-filter");
  const symbolKind = document.getElementById("api-symbol-kind");
  const symbolCount = document.getElementById("api-symbol-count");
  const symbolRows = Array.from(document.querySelectorAll("[data-api-symbol]"));
  if (symbolFilter && symbolKind && symbolCount && symbolRows.length) {
    const filterSymbols = () => {
      const query = symbolFilter.value.trim().toLocaleLowerCase();
      const kind = symbolKind.value;
      let visible = 0;
      symbolRows.forEach((row) => {
        const rowKind = row.dataset.symbolKind || "";
        const matchesKind =
          !kind || rowKind === kind || (kind === "class" && rowKind.endsWith("class"));
        const matchesQuery =
          !query || (row.dataset.symbolSearch || "").includes(query);
        row.hidden = !(matchesKind && matchesQuery);
        if (!row.hidden) visible += 1;
      });
      symbolCount.textContent = `${visible} ${visible === 1 ? "symbol" : "symbols"}`;
    };
    symbolFilter.addEventListener("input", filterSymbols);
    symbolKind.addEventListener("change", filterSymbols);
  }

  const revealHashTarget = () => {
    if (!window.location.hash) return;
    const target = document.getElementById(
      decodeURIComponent(window.location.hash.slice(1)),
    );
    if (target instanceof HTMLDetailsElement) target.open = true;
  };
  window.addEventListener("hashchange", revealHashTarget);
  revealHashTarget();

  const search = document.querySelector('[data-md-component="search"]');
  if (search) {
    const filterSearchResults = () => {
      search.querySelectorAll(".md-search-result__item").forEach((item) => {
        const link = item.querySelector("a[href]");
        if (!link) return;
        const target = new URL(link.href, window.location.href);
        item.hidden = languageForPath(target.pathname) !== language;
      });
    };
    new MutationObserver(filterSearchResults).observe(search, {
      childList: true,
      subtree: true,
    });
    filterSearchResults();
  }
})();
