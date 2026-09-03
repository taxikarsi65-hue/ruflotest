(() => {
  "use strict";

  /* ---------- mobile menu ---------- */
  const burger = document.getElementById("burger");
  const nav = document.getElementById("main-nav");

  if (burger && nav) {
    burger.addEventListener("click", () => {
      const open = nav.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", String(open));
      burger.setAttribute("aria-label", open ? "Zavřít menu" : "Otevřít menu");
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("is-open");
        burger.setAttribute("aria-expanded", "false");
      });
    });
  }

  /* ---------- sticky header shrink on scroll ---------- */
  const header = document.getElementById("site-header");
  let lastScroll = 0;
  window.addEventListener(
    "scroll",
    () => {
      const y = window.scrollY;
      if (header) header.style.boxShadow = y > 12 ? "0 8px 30px -18px rgba(0,0,0,.5)" : "none";
      lastScroll = y;

      const fab = document.querySelector(".fab");
      if (fab) fab.classList.toggle("is-visible", y > 400);
    },
    { passive: true }
  );

  /* ---------- active nav link on scroll ---------- */
  const navLinks = document.querySelectorAll("[data-nav]");
  const sections = Array.from(navLinks)
    .map((l) => document.querySelector(l.getAttribute("href")))
    .filter(Boolean);

  if (sections.length) {
    const navObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const id = "#" + entry.target.id;
          const link = document.querySelector(`[data-nav][href="${id}"]`);
          if (!link) return;
          if (entry.isIntersecting) {
            navLinks.forEach((l) => l.classList.remove("active"));
            link.classList.add("active");
          }
        });
      },
      { rootMargin: "-40% 0px -50% 0px" }
    );
    sections.forEach((s) => navObserver.observe(s));
  }

  /* ---------- scroll reveal ---------- */
  const revealEls = document.querySelectorAll(".reveal, .reveal-line");
  revealEls.forEach((el) => {
    const delay = el.getAttribute("data-delay");
    if (delay !== null) el.style.setProperty("--d", delay);
  });

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
  );
  revealEls.forEach((el) => revealObserver.observe(el));

  /* ---------- counters ---------- */
  const counters = document.querySelectorAll("[data-count]");
  const animateCount = (el) => {
    const target = parseInt(el.getAttribute("data-count"), 10);
    const suffix = el.getAttribute("data-suffix") || "";
    const duration = 1100;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.round(target * eased);
      el.innerHTML = value + suffix;
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  const countObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          countObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.6 }
  );
  counters.forEach((el) => countObserver.observe(el));

  /* ---------- price calculator ---------- */
  const calc = {
    hourly: 890,
    floorFee: 100,
  };
  const hoursInput = document.getElementById("calc-hours");
  const hoursValue = document.getElementById("calc-hours-value");
  const zoneSelect = document.getElementById("calc-zone");
  const helperInputs = document.querySelectorAll('input[name="calc-helper"]');
  const floorField = document.getElementById("calc-floor-field");
  const floorInput = document.getElementById("calc-floor");
  const floorValue = document.getElementById("calc-floor-value");
  const totalEl = document.getElementById("calc-total");
  const breakdownEl = document.getElementById("calc-breakdown");
  const calcCta = document.getElementById("calc-cta");

  const zoneLabels = {
    0: "Jen po Ústí nad Labem",
    120: "Blízké okolí (do 15 km)",
    200: "Okolí Ústí (do 30 km)",
    350: "Region (30–60 km)",
    430: "Vzdálenější region (60–80 km)",
    500: "Praha / okolí do 100 km",
  };
  const helperLabels = {
    0: "Jen řidič",
    250: "Řidič, co přiloží ruku",
    350: "Řidič + samostatný nakladač",
    550: "Řidič i nakladač nosí spolu",
  };

  const fmtKc = (n) => n.toLocaleString("cs-CZ");

  function selectedHelper() {
    const checked = [...helperInputs].find((el) => el.checked);
    return checked ? parseInt(checked.value, 10) : 0;
  }

  function updateCalc() {
    if (!hoursInput || !totalEl) return;

    const hours = parseInt(hoursInput.value, 10);
    const zoneFee = parseInt(zoneSelect.value, 10);
    const helperRate = selectedHelper();
    const hasHelper = helperRate > 0;

    hoursValue.textContent = hours + " hod";

    floorInput.disabled = !hasHelper;
    floorField.classList.toggle("is-disabled", !hasHelper);
    if (!hasHelper) {
      floorInput.value = 0;
    }
    const activeFloors = hasHelper ? parseInt(floorInput.value, 10) : 0;
    const floorCost = activeFloors * calc.floorFee;
    floorValue.textContent = activeFloors === 0 ? "bez patra" : `${activeFloors}× — +${fmtKc(floorCost)} Kč`;

    const base = calc.hourly * hours;
    const helperCost = hasHelper ? helperRate * hours : 0;
    const total = base + zoneFee + helperCost + floorCost;

    totalEl.textContent = fmtKc(total);

    const rows = [
      [`Základní sazba (${hours} hod × 890 Kč)`, fmtKc(base) + " Kč"],
      [zoneLabels[zoneFee], zoneFee ? "+" + fmtKc(zoneFee) + " Kč" : "0 Kč"],
    ];
    if (hasHelper) {
      rows.push([`${helperLabels[helperRate]} (${hours} hod × ${helperRate} Kč)`, "+" + fmtKc(helperCost) + " Kč"]);
      if (activeFloors > 0) {
        rows.push([`Patro bez výtahu (${activeFloors}×)`, "+" + fmtKc(floorCost) + " Kč"]);
      }
    }

    breakdownEl.innerHTML = rows.map(([label, value]) => `<li><span>${label}</span><span>${value}</span></li>`).join("");

    if (calcCta) {
      const summaryParts = [`${hours} hod`, zoneLabels[zoneFee], helperLabels[helperRate].toLowerCase()];
      if (activeFloors) summaryParts.push(`patro ${activeFloors}×`);
      calcCta.dataset.summary = `Orientační kalkulace: ${summaryParts.join(", ")} — cca ${fmtKc(total)} Kč.`;
    }
  }

  [hoursInput, zoneSelect, floorInput, ...helperInputs].forEach((el) => {
    if (el) el.addEventListener("input", updateCalc);
  });
  updateCalc();

  if (calcCta) {
    calcCta.addEventListener("click", () => {
      const textarea = document.querySelector('textarea[name="co_vezeme"]');
      if (textarea && calcCta.dataset.summary && !textarea.value) {
        textarea.value = calcCta.dataset.summary;
      }
    });
  }

  /* ---------- faq: close others when one opens ---------- */
  const faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach((item) => {
    item.addEventListener("toggle", () => {
      if (item.open) {
        faqItems.forEach((other) => {
          if (other !== item) other.open = false;
        });
      }
    });
  });

  /* ---------- smooth anchor offset for sticky header ---------- */
  const headerHeight = () => (header ? header.offsetHeight : 0);
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const id = anchor.getAttribute("href");
      if (!id || id === "#") return;
      const target = document.querySelector(id);
      if (!target) return;
      e.preventDefault();
      const top = target.getBoundingClientRect().top + window.scrollY - headerHeight() + 1;
      window.scrollTo({ top, behavior: "smooth" });
    });
  });
})();
