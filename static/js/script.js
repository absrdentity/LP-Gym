document.addEventListener("scroll", () => {
  const navbar = document.getElementById("navbar");
  navbar.classList.toggle("scrolled", window.scrollY > 80);
});

// ---------- Navbar background scroll effect ----------
const navbar = document.getElementById("navbar");

window.addEventListener("scroll", () => {
  if (window.scrollY > 50) {
    navbar.classList.add("scrolled");
  } else {
    navbar.classList.remove("scrolled");
  }
});


// ---------- Active nav link based on scroll ----------
const sections = document.querySelectorAll("section, .hero, footer");
const navLinks = document.querySelectorAll("#navbarNav a");

window.addEventListener("scroll", () => {
  let current = "";

  sections.forEach(section => {
    const sectionTop = section.offsetTop - 150;
    const sectionHeight = section.clientHeight;
    
    if (pageYOffset >= sectionTop && pageYOffset < sectionTop + sectionHeight) {
      current = section.getAttribute("id");
    }
  });

  navLinks.forEach(link => {
    link.classList.remove("active");
    if (link.getAttribute("href") === "#" + current) {
      link.classList.add("active");
    }
  });
});
